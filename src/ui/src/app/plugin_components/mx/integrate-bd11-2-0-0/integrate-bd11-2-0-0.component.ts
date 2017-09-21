import { Component,
         ComponentFactory,
         ComponentFactoryResolver,
         Input,
         OnInit,
         ViewChild,
         ViewContainerRef } from '@angular/core';
import { MdDialog,
         MD_DIALOG_DATA } from '@angular/material';

import { ReplaySubject }   from 'rxjs/Rx';

import { WebsocketService } from '../../../shared/services/websocket.service';
import { GlobalsService } from '../../../shared/services/globals.service';

import { RunDialogComponent } from '../run-dialog/run-dialog.component';
import { ReintegrateDialogComponent } from '../reintegrate-dialog/reintegrate-dialog.component';

// Import analysis plugin components here
import * as mx from '../';
var analysis_values = [];
var analysis_components = {};
for (let key in mx) {
  // console.log(key);
  if (key.match('Analysis')) {
    // console.log('YES');
    analysis_values.push(mx[key]);
    analysis_components[key.toLowerCase()] = mx[key];
  }
}

@Component({
  selector: 'app-integrate-bd11-2-0-0',
  templateUrl: './integrate-bd11-2-0-0.component.html',
  styleUrls: ['./integrate-bd11-2-0-0.component.css']
})
export class IntegrateBd11200Component implements OnInit {

  objectKeys = Object.keys;
  @Input() current_result: any;
  incomingData$: ReplaySubject<string>;

  full_result: any;
  selected_plot: string;
  view_mode: string = 'summary';
  data:any = {
    lineChartType: 'line',
    lineChartOptions: {
      animation: {
        duration: 500,
      },
      elements: {
        line: {
          tension: 0, // disables bezier curves
        },
      },
      legend: {
        display: true,
        position: 'right',
        labels: {
          boxWidth: 3,
        },
      },
      responsive: true,
      scales: {
        yAxes: [{
          scaleLabel: {
            display: true,
            labelString: '',
          },
          ticks: {},
        }],
        xAxes: [{
          scaleLabel: {
            display: true,
            labelString: '',
          },
          ticks: {},
        }],
      },
      tooltips: {
        callbacks: {}
      },
    },
  };

  // @ViewChild(BaseChartDirective) private _chart;
  @ViewChild('analysistarget', { read: ViewContainerRef }) analysistarget;
  analysis_component: any;

  constructor(private componentfactoryResolver: ComponentFactoryResolver,
              private websocket_service: WebsocketService,
              private globals_service: GlobalsService,
              public dialog: MdDialog) { }

  ngOnInit() {
    // Subscribe to results for the displayed result
    this.incomingData$ = this.websocket_service.subscribeResultDetails(
      this.current_result.result_type,
      this.current_result.result_id);
    this.incomingData$.subscribe(x => this.handleIncomingData(x));
  }

  public handleIncomingData(data: any) {
    console.log('handleIncomingData', data);
    this.full_result = data;

    // Select the default plot to show
    if ('Rmerge vs Frame' in data.results.plots) {
      this.selected_plot = 'Rmerge vs Frame';
      this.setPlot('Rmerge vs Frame');
    }
  }

  // Display the header information
  displayRunInfo() {

    let config = {
      width: '450px',
      height: '500px',
      data: this.full_result };

    let dialogRef = this.dialog.open(RunDialogComponent, config);
  }

  onViewModeSelect(view_mode:string) {

    var self = this;

    console.log(view_mode);

    setTimeout(function() {
      if (view_mode === 'analysis') {
        // If there is analysis data, determine the component to use
        if (self.full_result.results.analysis) {

          let plugin = self.full_result.results.analysis.plugin;
          const component_name = (plugin.type + plugin.id + plugin.version.replace(/\./g, '') + 'component').toLowerCase();
          console.log(component_name);
          console.log(analysis_components);

          // Create a componentfactoryResolver instance
          const factory = self.componentfactoryResolver.resolveComponentFactory(analysis_components[component_name]);

          // Create the component
          self.analysis_component = self.analysistarget.createComponent(factory);
          console.log(self.analysistarget);
          // Set the component current_result value
          // component.instance.current_result = event.value;
          self.analysis_component.instance.result = self.full_result.results.analysis;
        }
      }
    }, 100);
  }

  onPlotSelect(plot_key:string) {

    console.log('onPlotSelect', plot_key);
    this.setPlot(plot_key);

  }

  // Set up the plot
  setPlot(plot_key:string) {

    console.log('setPlot', plot_key);

    let plot_result = this.full_result.results.plots[plot_key];

    // Consistent features
    this.data.xs = plot_result.x_data;
    this.data.ys = plot_result.y_data;
    this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = plot_result.parameters.ylabel;
    this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = plot_result.parameters.xlabel;

    switch (plot_key) {

      case 'Rmerge vs Frame':
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        // Axis options
        // this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = function(data){
        //   var xLabels = data.ticks;
        //   xLabels.forEach(function (labels, i) {
        //       if (i % 10 !== 0){
        //           xLabels[i] = '';
        //       }
        //   });
        //   // xLabels.push('360');
        // };
        break;

      case 'Imean/RMS scatter':
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        break;

      case 'Anomalous & Imean CCs vs Resolution':
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        break;

      case 'RMS correlation ratio':
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        break;

      case "I/sigma, Mean Mn(I)/sd(Mn(I))":
        // Make the x labels in 1/A
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = function(data){
              var xLabels = data.ticks;
              xLabels.forEach(function (labels, i) {
                xLabels[i] = '1/'+(1.0/xLabels[i]).toFixed(2).toString();
              });
        };
        break;

      case "rs_vs_res":
        // Make the x labels in A
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = function(data){
              var xLabels = data.ticks;
              xLabels.forEach(function (labels, i) {
                xLabels[i] = (1.0/xLabels[i]).toFixed(2);
              });
        };
        break;

      case "Average I, RMS deviation, and Sd":
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        break;

      case 'Completeness':
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        break;

      case 'Redundancy':
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        break;

      case 'Radiation Damage':
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
        break;

      default:
        this.data = false;
    }
    console.log(this.data);
  }

  openReintegrateDialog() {

    let config = {
      width: '450px',
      height: '500px',
      data: this.full_result };

    let dialogRef = this.dialog.open(ReintegrateDialogComponent, config);

  }

  // Change the current result's display to 'pinned'
  pinResult(result) {
    result.display = 'pinned';
    this.websocket_service.updateResult(result);
  }

  // Change the current result's display to undefined
  undefResult(result) {
    result.display = '';
    this.websocket_service.updateResult(result);
  }

  // change the current result's display status to 'junked'
  junkResult(result) {
    result.display = 'junked';
    this.websocket_service.updateResult(result);
  }

}