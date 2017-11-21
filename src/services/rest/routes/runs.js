var express = require('express');
var router = express.Router();

// MongoDB model
var Run = require('../models/run');

// Routes that end with runs
// -----------------------------------------------------------------------------
// route to return image data given an id (GET api/runs/:run_id)
router.route('/runs/:run_id')
  .get(function(req, res) {

    Run.
      findOne({_id:req.params.run_id}).
      exec(function(err, run) {
        if (err) {
          console.error(err);
          res.status(500).json({
            success: false,
            message: err
          });
        } else {
          // Do not return the password
          for (let user of users) {
            user.password = undefined;
          }
          console.log('Returning run', run);
          res.status(200).json({
            success: true,
            run: run
          });
        }
      });
  });

module.exports = router;