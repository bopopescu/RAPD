"""
This file is part of RAPD

Copyright (C) 2011-2018, Cornell University
All rights reserved.

RAPD is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, version 3.

RAPD is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

__created__ = "2011-12-09"
__maintainer__ = "Jon Schuermann"
__email__ = "schuerjp@anl.gov"
__status__ = "Production"

#Required params for script to run.
WORK_DIR = '/home/schuerjp/temp/beamcenter'
#Known SG for images. P4 assumes lysozyme or thaumatin.
#SPACEGROUP = None
SPACEGROUP = 'P222'
##Number of labelit runs to fine tune beam center and spacing from original
#Jobs per distance will be (ITERATIONS+1)^2. 
#ITERATIONS = 10
ITERATIONS = 1
#Copy images to RAM on all cluster nodes
RAM = False

import warnings
#Remove stupid warnings about sha and md5.
with warnings.catch_warnings():
  warnings.filterwarnings("ignore", category=Warning)
  from multiprocessing import Process, Queue
  from threading import Thread
  import os
  import time, shutil, numpy, decimal, copy
  import utils.xutils as Utils
  from utils.modules import load_module
  #Used to get path of running file
  from inspect import getsourcefile

class FindBeamCenter(Process):
  def __init__(self, inp, output, logger=None):
    logger.info('FindBeamCenter.__init__')
    self.st = time.time()
    self.input,self.cpu,self.verbose,self.clean = inp
    self.output                             = output
    self.logger                             = logger
    
    # Store passed-in variables
    #self.site = site
    #self.command = command
    self.reply_address = self.input["return_address"]

    # Setting up data input
    self.setup = self.input["directories"]
    self.header = self.input["header1"]
    self.header2 = self.input.get("header2", False)
    self.site_parameters = self.input.get("site_parameters")
    self.preferences = self.input.get("preferences", {})
    self.controller_address = self.reply_address
    
    # Setup the weird named rapd_agent_index+strategy pipeline
    self.Labelit = load_module(seek_module="rapd_agent_index+strategy",
                                directories=('agents'),
                                logger=self.logger)
    # Setup the proper computer cluster for site.
    if self.site_parameters.get('cluster_site', False):
      self.Cluster = load_module(seek_module=self.site_parameters.get('cluster_site') ,
                                 directories=('sites.cluster'),
                                 logger=self.logger)
    else:
      self.Cluster = load_module(seek_module=self.site_parameters.get('img_site') ,
                                 directories=('sites.cluster'),
                                 logger=self.logger)
    
    #Number of labelit runs to fine tune beam center and spacing from original
    #Should be even number for symmetry around original beam center
    self.iterations2                        = ITERATIONS
    self.iterations2_space                  = 0.3
    #self.iterations2                        = 15
    #self.iterations2_space                  = 0.1
    #Sets the limit of the std dev (mm) of either x or y beam position in the top 10% of the solutions.
    #self.std_dev                            = 0.1
    self.std_dev                            = 0.25
    
    #Sets settings to check output on my machine and does not send results to database.
    self.cluster_use =  self.Cluster.check_cluster()
    #self.test = True
    if self.cluster_use:
      self.test                           = False
    else:
      self.test                           = True

    #this is where I have chosen to place my results
    self.labelit_results                    = {}
    self.labelit_summary                    = False
    #Labelit settings
    self.twotheta                           = False
    self.multiproc                          = True
    self.labelit_jobs                       = {}
    self.results                            = {}
    self.pool                               = {}
    self.new_input                          = {}
    #Settings for all programs
    self.x_beam         = self.header.get('beam_center_x')
    self.y_beam         = self.header.get('beam_center_y')
    self.working_dir    = self.setup.get('work')
    self.sg             = self.header.get('spacegroup','None')
    self.distance       = os.path.basename(self.working_dir)
    self.vendortype     = self.header.get('vendortype')
    
    Process.__init__(self,name='FindBeamCenter')
    self.start()
      
  def run(self):
    """
    Convoluted path of modules to run.
    """
    if self.verbose:
      self.logger.debug('FindBeamCenter::run')
    self.preprocess()
    
    self.sortJobs()
    
    self.processLabelit()
    self.queue()
    self.labelitSort()
    self.postprocess()
    
    
  def preprocess(self):
    """
    Setup the working dir in the RAM and save the dir where the results will go at the end.
    """ 
    if self.verbose:
      self.logger.debug('FindBeamCenter::preprocess')
    
    if os.path.exists(self.working_dir) == False:
      os.makedirs(self.working_dir)
    os.chdir(self.working_dir)
    #print out recognition of the program being used
    #self.PrintInfo()
      
  def processLabelit(self):
    """
    Labelit error correction. Set/reset setting in dataset_preferences.py according to error iteration.
    Commented out things were tried before.
    """
    if self.verbose:
      self.logger.debug('FindBeamCenter::processLabelit')
    try:
      params = {}
      params['test'] = self.test
      params['cluster'] = self.Cluster
      params['cluster_queue'] = self.Cluster.check_queue(self.input.get('command'))
      params['vendortype'] = self.vendortype
      params['iterations'] = 1
      #if self.vendortype in ['Pilatus-6M','ADSC-HF4M']:
      #  params['iterations'] = 1
      #else:
      #  params['iterations'] = 4
      params['verbose'] = False
      
      #Have to add to the sleep as more runs are submitted
      add_time = 2*len(self.new_input.keys())/10000
      for name in self.new_input.keys():
        self.pool[name] = Queue()
        job = Process(target=self.Labelit.RunLabelit,args=(self.new_input[name],self.pool[name],params,self.logger))
        job.start()
        self.labelit_jobs[job] = name
        #Have to do a small sleep otherwise jobs lock and take >10s to submit jobs to cluster??
        #The problem builds with more iterations to run.
        #time.sleep(0.05 + add_time)
	time.sleep(0.1)
      #Send back message to say when all jobs are submitted.
      #self.output.put('done')

    except:
      self.logger.exception('**Error in FindBeamCenter::processLabelit**')
  
  def queue(self):
    """
    Queue for Labelit.
    """
    if self.verbose:
      self.logger.debug('FindBeamCenter::queue')
    try:
      counter = len(self.labelit_jobs.keys())
      while counter != 0:
        for job in self.labelit_jobs.keys():
          if job.is_alive() == False:
            if self.labelit_results.has_key(self.labelit_jobs[job]):
              self.labelit_results[self.labelit_jobs[job]].update(self.pool[self.labelit_jobs[job]].get())
            else:
              self.labelit_results[self.labelit_jobs[job]] = self.pool[self.labelit_jobs[job]].get()
            #clean up folders
            if self.clean:
              if os.path.exists(os.path.join(self.working_dir,self.labelit_jobs[job])):
                shutil.rmtree(os.path.join(self.working_dir,self.labelit_jobs[job]),ignore_errors=True)
            del self.labelit_jobs[job]
            counter -= 1
        time.sleep(2)
      #Send back message to say when all jobs are submitted.
      self.output.put('done')
    
    except:
      self.logger.exception('**Error in FindBeamCenter.queue**')

  def postprocessJobs(self,inp):
    """
    Update the labelit results.
    """
    if self.verbose:
      self.logger.debug('FindBeamCenter::postprocessJobs')
    try:
      if inp != None:
        for key in inp:
          if self.labelit_results.has_key(key):
            self.labelit_results[key].update(inp[key])
          else:
            self.labelit_results[key] = inp[key]
            
    except:
      self.logger.exception('**Error in FindBeamCenter.postprocessJobs**')
  
  def postprocess(self):
    """
    Finish everything up.
    """
    if self.verbose:
      self.logger.debug('FindBeamCenter::postprocess')
    try:
      #Send back results
      self.output.put(self.results)
      #Cleanup folders
      if self.clean:
        #If images in RAM then delete. Could put in handler and run once...
        if RAM == True:
          if self.header.get('fullname').startswith('/dev/shm'):
            Utils.rocksCommand('rm -rf %s'%self.header.get('fullname'),self.logger)
          if self.header2:
            if self.header2.get('fullname').startswith('/dev/shm'):
              Utils.rocksCommand('rm -rf %s'%self.header2.get('fullname'),self.logger)
        #Cleanup folders in working dir.
        shutil.rmtree(self.working_dir,ignore_errors=True)
            
    except:
      self.logger.exception('**Error in FindBeamCenter.postprocess**')
  
  def sortJobs(self):
    """
    Decides how many Labelit jobs to run and sorts them among the processors available.
    """
    if self.verbose:
      self.logger.debug('FindBeamCenter::sortJobs')
    try:
      #inp = {}
      #Save initial beam center.
      orig_x = self.x_beam
      orig_y = self.y_beam
      if self.preferences.has_key('x_beam'):
        del self.preferences['x_beam']
      if self.preferences.has_key('y_beam'):
        del self.preferences['y_beam']
      
      #Calculate new beam centers and save them.
      med = int(self.iterations2/2)
      for x in range(self.iterations2+1):
        if x <= med:
          new_x_beam = float(orig_x)-x*self.iterations2_space
        else:
          new_x_beam = float(orig_x)+(x-med)*self.iterations2_space
        for y in range(self.iterations2+1):
          if y <= med:
            new_y_beam = float(orig_y)-y*self.iterations2_space
          else:
            new_y_beam = float(orig_y)+(y-med)*self.iterations2_space
          name = 'bc_%s_%s'%(x,y)
          #Start the results by saving the new beam center.
          self.labelit_results[name] = {'beam_X': str(new_x_beam),'beam_Y': str(new_y_beam)}
          #Save the working path and new beam center to new input. 
          new_input = {'command': self.input['command']}
	  new_input.update({'directories': {'work':os.path.join(os.getcwd(),name)}})
	  new_input['header1'] = self.input['header1'].copy()
	  new_input['header1']['beam_center_x'] = str(new_x_beam)
	  new_input['header1']['beam_center_y'] = str(new_y_beam)
	  if self.header2:
	    new_input['header2'] = self.input['header2'].copy()
	    new_input['header2']['beam_center_x'] = str(new_x_beam)
	    new_input['header2']['beam_center_y'] = str(new_y_beam)
	  new_input['site_parameters'] = self.site_parameters
	  new_input['preferences'] = self.preferences
	  new_input['return_address'] = self.reply_address
	  self.new_input[name] = new_input
      #Utils.pp(self.new_input)

    except:
      self.logger.exception('**ERROR in FindBeamCenter.sortJobs**')

  def labelitSort(self):
    """
    Figure out which round has the best index fit.
    """
    if self.verbose:
      self.logger.debug('FindBeamCenter::labelitSort')
    
    try:
      li = []
      stats = {}
      passed = True
      orig_sg = 1
      if self.sg == None:
        find_sg = True
      else:
        find_sg = False
      tr = len(self.labelit_results.keys())
      #Label the SG and grab the solutions with the highest SG.
      for i in range(0,2):
        for run in self.labelit_results.keys():
          if run.startswith('bc_'):
            if type(self.labelit_results[run].get("labelit_results")) == dict:
	      if i == 0:
                #Check for pseudotranslation, meaning bad snap!!!
                if self.labelit_results[run].get("labelit_results").get('pseudotrans'):
                  #passed = False
                  pass
                #Get Labelit stats and SG#
                Utils.getLabelitStats(self,run)
                sg = self.labelit_results[run].get('labelit_stats').get('best').get('SG')
		new_sg = float(Utils.convertSG(self,sg))
                self.labelit_results[run].update({'labelit_best_sg#': new_sg})
                if find_sg:
                  if new_sg > orig_sg:
                    self.sg = sg
                    orig_sg = new_sg
              else:
                #Make sure I compare same SG.
                if self.labelit_results[run].get('labelit_stats').get('best').get('SG') == self.sg:
                  li.append(run)
                else:
                  del self.labelit_results[run]
      #Calculate the number of solutions for 10% of correct SG and check if enough are present.
      l = len(li)
      if l > 0:
        top = int(round(l*0.1))
        if top < 5:
          if l < top:
            top = l
          else:
            top = 5
        """
        #Does not seem to matter.
        test = decimal.Decimal(l)/decimal.Decimal(len(runs))
        if test < decimal.Decimal('0.1'):
            passed = False
        """
        #Print results for testing.
        #if self.verbose:
        #print 'Iteration=',str(self.iteration)
        """
        print 'Total number of Labelit runs: %s'%tr
        print 'Total number of solutions in %s: %s'%(self.sg, l)
        print 'Number of solutions in the top 10%% = %s'%top
        """
        self.logger.debug('Total number of Labelit runs: %s'%tr)
        self.logger.debug('Total number of solutions in %s: %s'%(self.sg, l))
        self.logger.debug('Number of solutions in the top 10%% = %s'%top)
        #Sort solutions in correct SG by each param
        ls = [("self.labelit_results[run].get('labelit_stats').get('P1').get('rmsd')","Labelit P1 RMSD"),
              ("self.labelit_results[run].get('labelit_stats').get('P1').get('mos_rms')","Mosflm P1 RMS"),
              ("self.labelit_results[run].get('labelit_stats').get('best').get('metric')","Labelit Metric"),
              ("self.labelit_results[run].get('labelit_stats').get('best').get('rmsd')","Labelit RMSD"),
              ("self.labelit_results[run].get('labelit_stats').get('best').get('mos_rms')","Mosflm RMS")]
        for z in range(len(ls)):
          dict1 = {}
          for run in li:
            dict1[run] = float(eval(ls[z][0]))
          li1 = dict1.values()
          li1.sort()
          #Grab the top 10%.
          li1_top = li1[:top]
          li2 = []
          for run in li:
            for line in li1_top:
              if dict1[run] == line:
                li2.append(run)
                li1_top.remove(line)
                if line == li1[0]:
                  top1 = run
          #Grab the Labelit beam centers and calculate the stats.
          x = []
          y = []
          for run in li2:
            x.append(float(self.labelit_results[run].get("labelit_results").get('labelit_bc').get('labelit_x_beam')))
            y.append(float(self.labelit_results[run].get("labelit_results").get('labelit_bc').get('labelit_y_beam')))
          stats[ls[z][1]] = {'avg_x': numpy.average(x), 'std_x': numpy.std(x), 'avg_y': numpy.average(y), 'std_y': numpy.std(y),
                             'sum_std': numpy.std(x)+numpy.std(y), 'j1': ls[z][0], 'top': top1}
        #Sort all results by lowest sum of std dev (x+y) and save the best.
        temp = []
        for i in range(2):
          for key in stats.keys():
            if i == 0:
              #First, save the lowest sum_std.
              temp.append(stats[key].get('sum_std'))
            else:
              if stats[key].get('sum_std') == temp[0]:
                #Check the std dev. 
                if decimal.Decimal(str(stats[key].get('std_x'))) > decimal.Decimal(str(self.std_dev)):
                  passed = False
                if decimal.Decimal(str(stats[key].get('std_y'))) > decimal.Decimal(str(self.std_dev)):
                  passed = False
                #Save best results for each distance for further calculations.
                self.results['orig_X'] = self.x_beam
                self.results['orig_Y'] = self.y_beam
                self.results['X'] = stats[key].get('avg_x')
                self.results['Y'] = stats[key].get('avg_y')
                self.results['passed'] = passed
                #best = stats[key].get('top')
                #if self.verbose:
                """
                print '****************************************'
                print 'At %s mm:'%self.distance
                print 'Best stats from %s'%key
                print 'X =%s std=%s'%(stats[key].get('avg_x'),stats[key].get('std_x'))
                print 'Y =%s std=%s'%(stats[key].get('avg_y'),stats[key].get('std_y'))
                print 'Good results=%s'%passed
                print '****************************************'
                """
                self.logger.debug('****************************************')
                self.logger.debug('At %s mm:'%self.distance)
                self.logger.debug('Best stats from %s'%key)
                self.logger.debug('X =%s std=%s'%(stats[key].get('avg_x'),stats[key].get('std_x')))
                self.logger.debug('Y =%s std=%s'%(stats[key].get('avg_y'),stats[key].get('std_y')))
                self.logger.debug('Good results=%s'%passed)
                self.logger.debug('****************************************')
                break
          if i == 0:
            temp.sort()
      else:
        self.results = {'passed':False}
            
    except:
      self.logger.exception('**ERROR in FindBeamCenter.labelitSort**')
      self.results = {'passed':False}

#class Handler(threading.Thread,Communicate):
#class Handler(Process,Communicate):
#class Handler(Process):
class Handler(Thread):
  """
  Looks at the input to determine how to run the process. Runs the process and passes the results back.
  """
  def __init__(self,input,logger=None):
    logger.info('Handler.__init__')
    self.st = time.time()
    self.input                              = input
    if self.input == None:
      os._exit(0)
    self.logger                             = logger
    #Setting up data input
    #self.setup                              = self.input[1]
    #self.controller_address                 = self.input[-1]
    
    self.jobs                               = {}
    self.results                            = {}
    self.output                             = {}
    #Set a timer to limit length Labelit waits for results before aborting.
    self.timer                              = False
    #Cleanup all the folders and files after running.
    self.clean                              = False
    #Turn on verbose output.
    self.verbose                            = True
    
    """
    #******BEAMLINE SPECIFIC*****
    #Used to know when to send the results back to Core, otherwise sent to terminal.
    if self.input[-2].get('aperture',False):
      self.beamline_use                   = True
    else:
      self.beamline_use                   = False
    #******BEAMLINE SPECIFIC*****
    """
    self.beamline_use = False
    
    #initialize the thread
    #Process.__init__(self)
    Thread.__init__(self)
    self.start()
      
  def run(self):
    if self.verbose:
      self.logger.debug('Handler::run')
    self.process()
    self.queue()
    self.sort()
    self.postprocess()
  
  def process(self):
    """
    Create input dict and send to FindBeamCenter.
    """
    if self.verbose:
      self.logger.debug('Handler::process')
    try:
      #setup = self.setup.get('info')
      setup = self.input.get('info')
      """
      njobs = len(setup)
      cpu = multiprocessing.cpu_count()
      ncpu = cpu/njobs
      if ncpu == 0:
          ncpu = 1
      """
      #Seems to give best load and speed on our cluster.
      ncpu = 1
      od = self.input.get('directories').get('work')
      jobs = ['510.0']
      for job in jobs:
      #for job in setup.keys():
        new_input = {}
	new_input['command'] = self.input.get('command')
        #new_input.append(self.input[0])
        nd = os.path.join(od,job)
	new_input['directories'] = {'work':nd}
        #new_input.append({'work':nd})
        #for header in setup[job]:
          #new_input.append(header)
	for x in range(len(setup[job])):
	  n = str(x+1)
	  new_input['header'+n] = setup[job][x]
        #new_input.extend(self.input[-2:])
	new_input["preferences"] = self.input.get("preferences")
	new_input["site_parameters"] = self.input.get("site_parameters")
	new_input["return_address"] = self.input.get("return_address")
	# Setup the actual jobs
	self.output[job] = Queue()
        j = Process(target=FindBeamCenter,kwargs={'inp':(new_input,ncpu,self.verbose,self.clean),
                                                  'output':self.output[job],'logger':self.logger})
        j.start()
        self.jobs[j] = job
        #Wait for the previous jobs to be finished.
        self.output[job].get()
      #Utils.pp(new_input)
        
    except:
      self.logger.exception('**Error in Handler.process**')
  
  def queue(self):
    """
    Queue for jobs running.
    """
    if self.verbose:
        self.logger.debug('Handler::queue')
    try:
        timer = 0
        jobs = self.jobs.keys()
        if jobs != ['None']:
          counter = len(jobs)
          while counter != 0:
            for job in jobs:
              if job.is_alive() == False:
                jobs.remove(job)
                distance = self.jobs[job]
                self.logger.debug('Finished distance %s'%distance)
                self.results[distance] = self.output[distance].get()
                counter -= 1
            time.sleep(2)
            timer += 2
            if self.verbose:
              print 'Waiting for Labelit to finish %s seconds'%timer
            if self.timer:
              if timer >= self.timer:
                timed_out = True
                #Check folders to see why it timed out.
                self.clean = False
                break 
        self.logger.debug('Labelit finished.')

    except:
      self.logger.exception('**Error in Handler.queue**')
      
  def sort(self):
    """
    Sort results by distance for calculations.
    """
    if self.verbose:
      self.logger.debug('Handler::sort')
    try:
      """
      #Utils.pp(self,self.results)
      #Q315
      self.results = {   '400': {    #'X': 156.69,
                                     'X': 156.65,
                                     'Y': 155.72999999999999,
                                     'orig_X': '156.67',
                                     'orig_Y': '155.70',
                                     'passed': True},
                          '500_0': {   'X': 156.25799999999998,
                                       'Y': 155.61000000000001,
                                       'orig_X': '156.19',
                                       'orig_Y': '155.61',
                                       'passed': True},
                          '500_1': {   'X': 156.25799999999998,
                                       'Y': 155.61000000000001,
                                       'orig_X': '156.19',
                                       'orig_Y': '155.61',
                                       'passed': True},
                          '500_2': {   'X': 156.262,
                                       'Y': 155.61799999999999,
                                       'orig_X': '156.19',
                                       'orig_Y': '155.61',
                                       'passed': True},
                          '500_3': {   'X': 156.25,
                                       'Y': 155.61000000000001,
                                       'orig_X': '156.19',
                                       'orig_Y': '155.61',
                                       'passed': True},
                          '550': {   'X': 156.00200000000001,
                                     'Y': 155.57599999999999,
                                     'orig_X': '155.97',
                                     'orig_Y': '155.56',
                                     'passed': True}
                      }
      """
      #Separate out the same distance runs.
      res = {}
      new_res = {}
      for job in self.results.keys():
        if self.results[job].get('passed'):
          #If multiple runs at same distance.
          if job.count('_'):
            dis = job[:job.index('_')]
            if job.startswith(dis):
              if res.has_key(dis):
                l = []
                l.extend(res[dis])
                l.extend([job])
                res[dis] = l
              else:
                res[dis] = [job]
          else:
            new_res[int(float(job))] = self.results[job]
              
      #Calculate average and std. dev of same distance runs. Toss worst solution if std. dev > 0.1 and recalc average, if 3 or more at same distance.
      l = ['X','Y']
      for dis in res.keys():
        new_res[int(dis)] = {}
        for i in range(len(l)):
          recalc = False
          while 1:
            bp = []
            for run in res[dis]:
              bp.append(self.results[run].get(l[i]))
              orig = self.results[run].get('orig_%s'%l[i])
            avg = numpy.around(numpy.average(bp),decimals=2)
            std = numpy.std(bp)
            tmp = {l[i] : float(avg),'orig_%s'%l[i]:orig}
            new_res[int(float(dis))].update(tmp)
            #If at least 3 at same distance...
            if len(bp) > 2:
              if recalc:
                break
              else:
                if std > decimal.Decimal('0.1'):
                  recalc = True
                  junk = {}
                  for run in res[dis]:
                    x1 = self.results[run].get(l[i])
                    diff = numpy.absolute(x1-avg)
                    junk[diff] = run
                  l = junk.keys()
                  l.sort()
                  l.reverse()
                  for d in junk.keys():
                    if d == l[0]:
                      res[dis].remove(junk[d])
              if recalc == False:
                break
            else:
              break
      
      for dis in new_res.keys():
        #Remove 'passed' key
        if new_res[dis].has_key('passed'):
          del new_res[dis]['passed']
        for i in range(len(l)):
          #Figure out detector
          if new_res[dis].get(l[i]) > 200.0:
            pilatus = True
          else:
            pilatus = False
          #calculate beam shift.
          diff = new_res[dis].get(l[i]) - float(new_res[dis].get('orig_%s'%l[i]))
          new_res[dis].update({'diff_%s'%l[i] : str(diff)})
              
      #Calculate the 6th order polynomial from data if 3 or more distances present.
      if len(new_res.keys()) > 2:
        temp = {}
        #Write line for file to use for image header beam position (NE-CAT ONLY for CONSOLE).
        if pilatus:
          f = 'phi_bc_coeff.dat'
        else:
          f = 'phii_bc_coeff.dat'
        f1 = open(f,'w')
        for i in range(len(l)):
          d = new_res.keys()
          d.sort()
          bp = []
          for dis in d:
            bp.append(new_res[dis].get(l[i]))
          da = numpy.array(d)
          ba = numpy.array(bp)
          (AX,BX,CX,DX,EX,FX,GX) = numpy.polyfit(da,ba,6)
          temp['%s beam eq'%l[i]] = {"beam_center_%s_m6"%l[i].lower():AX,
                                     "beam_center_%s_m5"%l[i].lower():BX,
                                     "beam_center_%s_m4"%l[i].lower():CX,
                                     "beam_center_%s_m3"%l[i].lower():DX,
                                     "beam_center_%s_m2"%l[i].lower():EX,
                                     "beam_center_%s_m1"%l[i].lower():FX,
                                     "beam_center_%s_b"%l[i].lower():GX}
          print '%s %s %s %s %s %s %s\n'%(GX,FX,EX,DX,CX,BX,AX)
          f1.write('%s %s %s %s %s %s %s\n'%(GX,FX,EX,DX,CX,BX,AX))
        f1.close()
        new_res.update(temp)
        #Change ownership for SAMBA. DOESN'T WORK.
        #os.chown(f,'nobody','nobody')
      else:
        new_res['X beam eq'] = None
        new_res['Y beam eq'] = None
      
      #Overwrite self.results
      self.results = new_res
      #self.logger.debug(self.results)
           
    except:
      self.logger.exception('**Error in Handler.sort**')
  
  def postprocess(self):
    """
    Pass info back to the core.
    """
    if self.verbose:
      self.logger.debug('Handler::postprocess')
    try:
      #Summary.summaryLabelitBC(self)
      #self.htmlSummary()
      beam_status = {}
      beam_status['beam_status'] = 'SUCCESS'
      #Send back results
      try:
        """
	self.results.update(beam_status)
        if self.results:
          self.input.append(self.results)
        if self.beamline_use:
          self.sendBack2(self.input)
        else:
          Utils.pp(self.results)
          #Save results to file so it can be read in RunCLuster if needed.
          Utils.pp2((self.results,os.path.join(self.input[1].get('work'),'bc.log')))
	"""
	Utils.pp(self.results)
	#Save results to file so it can be read in RunCLuster if needed.
        #Utils.pp2((self.results,os.path.join(self.input[1].get('work'),'bc.log')))
	Utils.pp2((self.results,os.path.join(self.input['directories']['work'],'bc.log')))
	
      except:
        self.logger.exception('**Could not send results to pipe.**')
      
      #Say job is complete.
      t = round(time.time()-self.st)
      self.logger.debug('-------------------------------------')
      self.logger.debug('RAPD beam center complete.')
      self.logger.debug('Total elapsed time: %s seconds'%t)
      self.logger.debug('-------------------------------------')
      print '\n-------------------------------------'
      print 'RAPD beam center complete.'
      print 'Total elapsed time: %s seconds'%t
      print '-------------------------------------'
      #return(self.results)
      #sys.exit(0) #did not appear to end script with some programs continuing on for some reason.
      os._exit(0)
      #sys.exit(0)

    except:
      self.logger.exception('**Error in Handler.postprocess**')

class RunCluster(Thread):
  def __init__(self,inp,logger=None):
    logger.info('RunCluster.__init__')
    self.image_dir            = inp
    self.logger               = logger
    self.log = os.path.join(WORK_DIR,'bc.log')
    self.timer                = 600
    self.verbose              = True
    self.running              = False
    self.cluster_use          = False
    
    Thread.__init__(self)
    #start the thread
    self.start()
      
  def run(self):
    if self.verbose:
      self.logger.debug('RunCluster::run')
    
    self.conCluster()
    self.queue()
    
  def conCluster(self):
    """
    If not running on computer cluster, connect to node and launch.
    """
    try:
      #get path of running file
      fpath = os.path.abspath(getsourcefile(lambda:0))
      
      #command = '-pe smp 8 -o %s rapd.python /gpfs5/users/necat/rapd/gadolinium/trunk/rapd_agent_beamcenter.py %s'%(self.log,self.image_dir)
      #command = '-pe smp 8 -q phase2.q -o %s /gpfs6/users/necat/Jon/Programs/RAPD/bin/rapd.python /gpfs6/users/necat/Jon/Programs/CCTBX_x64/modules/rapd/src/rapd_agent_beamcenter.py %s'%(self.log,self.image_dir)
      command = '-pe smp 8 -q phase2.q -o %s rapd.python %s %s'%(self.log,fpath,self.image_dir)
      os.chdir(WORK_DIR)
      self.pid = BLspec.connectCluster(command)
      
    except:
      self.logger.exception('**Error in RunCluster::conCluster**')
      
  def queue(self):
    if self.verbose:
      self.logger.debug('RunCluster::queue')
    timer = 0
    while timer < self.timer:
      if BLspec.stillRunningCluster(self,self.pid) == False:
        self.postprocess()
        break
      time.sleep(1)
      timer += 1
          
  def postprocess(self):
    """
    Print the log to the screen
    """
    if self.verbose:
      self.logger.debug('RunCluster::postprocess')
    #Need to wait for it to be written to disk.
    time.sleep(2)
    for line in open(self.log,'r').readlines():
      print line.rstrip()
    l = [os.path.join(WORK_DIR,'phi_bc_coeff.dat'),os.path.join(WORK_DIR,'phii_bc_coeff.dat')]
    for x in range(len(l)):
      if os.path.exists(l[x]):
        for line in open(l[x],'r').readlines():
          print line.rstrip()

def calc_beamcenter(inp):
  x = 0.001202*inp + 150.03498
  y = -0.001318*inp + 149.80818
  return(x,y)       

def createInput(image_dir,site,logger):
  logger.debug('createInput')
  #import glob
  from iotbx.detectors import ImageFactory
  try:
    img_site_id, img_site, c_site, imgs = site
    l1 = []
    l2 = []
    d = {}
    pids = []
    vendortype = ImageFactory(imgs[0]).vendortype
    if vendortype == 'ADSC-HF4M':
      from detectors.rapd_adsc import Hf4mReadHeader as readHeader
    elif vendortype == 'Pilatus-6M':
      from detectors.rapd_pilatus import pilatus_read_header as readHeader
    elif  vendortype == 'ADSC':
      from detectors.rapd_adsc import Q315ReadHeader as readHeader
    else:
      from detectors.mar import MarReadHeader as readHeader
    l = [p for p in imgs if p.count('priming_shot') == False] #Remove priming shot (NE-CAT ONLY)
    for x in range(2):
      for i in l:
	if x == 0:
          #Get headers first
          header = readHeader(i)
          #Send images to ImageFactory to read the header (TODO).
          #Send images to RAM on all cluster nodes first.
          if RAM == True:
            image_path = os.path.join('/dev/shm',os.path.basename(header.get('fullname')))
            command = 'cp %s %s'%(header.get('fullname'),image_path)
            #ONLY work at NE-CAT
	    job = Process(target=Utils.rocksCommand,args=(command,logger))
            job.start()
            pids.append(job)
          else:
            image_path = header.get('fullname')
          x1,y1 = calc_beamcenter(round(header.get('distance')))
	  l1.append({#'beam_center_x' : round(header.get('beam_center_x'),3),
                     #'beam_center_y' : round(header.get('beam_center_y'),3),
		     #'beam_center_x' : 150.049, #BM
		     #'beam_center_y' : 151.148, #BM
		     #'beam_center_x' : 151.186, #ID
		     #'beam_center_y' : 144.821, #ID
		     #'beam_center_x' : 150.31, #BM
		     #'beam_center_y' : 149.53, #BM
		     'beam_center_x' : x1, #BM
		     'beam_center_y' : y1, #BM
		     'spacegroup'    : SPACEGROUP,
                     'fullname'      : image_path,
                     'distance'      : round(header.get('distance')),
                     'vendortype'    : vendortype,
                    })
        else:
          #Then sort by distance for input
          l3 = []
          if os.path.basename(i) not in (l2):
            for y in range(2):
              for z in range(len(l1)):
                if y == 0:
                  if os.path.basename(i) == os.path.basename(l1[z].get('fullname')):
                    dist = l1[z].get('distance')
                    l3.append(l1[z])
                    l2.append(os.path.basename(l1[z].get('fullname')))
                elif l1[z].get('distance') == dist:
                  if os.path.basename(l1[z].get('fullname')) not in l2:
                    l3.append(l1[z])
                    l2.append(os.path.basename(l1[z].get('fullname')))
            d[str(dist)] = tuple(l3[:2])
    #wait for images to be copied to RAM.
    if RAM == True:
      while len(pids) != 0:
        for job in pids:
          if job.is_alive() == False:
            pids.remove(job)
        time.sleep(1)

    inp = {'directories': {'work': WORK_DIR},
           'info' : d,
	   'command' : 'INDEX+STRATEGY',
	   'preferences': {"sample_type": "Protein","beam_flip": "False","multiprocessing":"True",
                           "a":0.0,"b":0.0,"c":0.0,"alpha":0.0,"beta":0.0,"gamma":0.0},
	   'site_parameters': {'img_site_id': img_site_id,
	                       'img_site': img_site,
			       'cluster_site': c_site},
	   'return_address': ("127.0.0.1", 50000)
          }
    Utils.pp(inp)
    return(inp)
  
  except:
      logger.exception('**Error in Handler.postprocess**')
      print 'Could not create input script from folder specified!'
      return(None)

def sort_dir(image_dir):
  import glob
  #check for different image suffixes in the folder.
  _l = ['*.cbf','*.img','*.[0-9]*']
  for x in range(len(_l)):
    l = glob.glob(os.path.join(image_dir,_l[x]))
    if len(l) != 0:
      break
  l.sort()
  return (l)
  
def load_cluster(image_dir):
  """
  Load the computer cluster module so the job can be submitted.
  """
  # Determine the site and load cluster. May be different from where images are from...
  # Check the images
  imgs = sort_dir(image_dir)
  site = Utils.get_site(imgs[0],False)
  cluster_site_name = os.getenv('RAPD_SITE1', False)
  # Determine the site by env variable first.
  if cluster_site_name:
    cluster_site_name = cluster_site_name.lower()
    cluster_site = load_module(seek_module=cluster_site_name, directories='sites')
  else:
    # Otherwise use the image origin as site.
    cluster_site = load_module(seek_module=site[0], directories='sites')
  cluster = load_module(cluster_site.CLUSTER_ADAPTER)
  out = (site[1], site[0], cluster_site_name, imgs)
  return ((out, cluster))
  

def main():
  """
  This pipeline has to be run on a computer cluster. It launches many Labelit autoindexing runs varying input beamcenter
  for each distance, then looks at all the refined beam center outputs and fits to a 6th order polymonial.
  """
  #start logging
  import utils.log
  logger = utils.log.get_logger(logfile_dir=WORK_DIR,)
  
  #Parse the command line for commands.
  import argparse
  parser = argparse.ArgumentParser(description='Run job on computer cluster.')
  parser.add_argument('inp' ,nargs='*', type=str, help='folder')
  args = vars(parser.parse_args())
  if len(args['inp']) == 0:
    image_dir = raw_input('In what folder do the direct beam shots exist?: ')
  else:
    image_dir = args['inp'][0]
    
  #cluster = load_cluster(image_dir)
  (site_info, cluster) = load_cluster('/home/schuerjp/temp/beamcenter/images/BM')
  #createInput('/home/schuerjp/temp/beamcenter/images',c_site_name, logger)
  #createInput('/home/schuerjp/temp/beamcenter/images', site_info, logger)
  #createInput('/home/schuerjp/temp/beamcenter/images/BM',site_info, logger)
  Handler(createInput('/home/schuerjp/temp/beamcenter/images/BM',site_info, logger),logger=logger)
  """
  if cluster.check_cluster():
    #Creates the input dict and passes it to the Handler.
    Handler(createInput(image_dir, cluster_site_name, logger),logger=logger)
  else:
    #Connect to the cluster and rerun this script if not launched on computer cluster.
    RunCluster(image_dir,logger=logger)
  """
if __name__ == '__main__':
  main()
