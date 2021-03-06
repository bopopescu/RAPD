import { Component, Input, OnDestroy, OnInit } from "@angular/core";

import { MatDialog, MAT_DIALOG_DATA } from "@angular/material/dialog";
import { MatToolbarModule } from "@angular/material/toolbar";

import { ReplaySubject } from "rxjs/Rx";

import { WebsocketService } from "../../../shared/services/websocket.service";
import { RestService } from "../../../shared/services/rest.service";
import { GlobalsService } from "../../../shared/services/globals.service";

import { HeaderDialogComponent } from "../header-dialog/header-dialog.component";
import { ReindexDialogComponent } from "./reindex-dialog/reindex-dialog.component";
import { DialogSelectProjectComponent } from "../../../shared/components/dialog-select-project/dialog-select-project.component";

@Component({
  selector: "app-index-3b34-2-0-0",
  templateUrl: "./index-3b34-2-0-0.component.html",
  styleUrls: ["./index-3b34-2-0-0.component.css"]
})
export class Index3b34200Component implements OnInit, OnDestroy {
  @Input() current_result: any;

  incomingData$: ReplaySubject<string>;

  full_result: any = { process: { status: 0 }, results: {} };

  view_mode: string = "summary";

  selected_plot: string;
  selected_plot_label: string;
  plot_select_labels: any = {
    // 'background':'Background',
    // 'exposure':'Exposure',
    osc_range: "Osc Range NORM",
    osc_range_anom: "Osc Range ANOM",
    max_delta_omega: "Max Oscillation",
    rad_damage: "Radiation Damage",
    wilson: "Wilson"
  };

  data: any = {
    lineChartType: "line",
    lineChartOptions: {
      animation: {
        duration: 500
      },
      elements: {
        line: {
          tension: 0 // disables bezier curves
        }
      },
      legend: {
        display: true,
        position: "right",
        labels: {
          boxWidth: 3
        }
      },
      responsive: true,
      scales: {
        yAxes: [
          {
            scaleLabel: {
              display: true,
              labelString: ""
            },
            ticks: {}
          }
        ],
        xAxes: [
          {
            scaleLabel: {
              display: true,
              labelString: ""
            },
            ticks: {}
          }
        ]
      },
      tooltips: {
        callbacks: {}
      }
    }
  };

  objectKeys = Object.keys;
  objectToArray(input: any): [any] {
    return [].concat.apply(
      [],
      Object.keys(input).map(function(key, index) {
        return input[key];
      })
    );
  }

  constructor(
    private websocket_service: WebsocketService,
    private rest_service: RestService,
    private globals_service: GlobalsService,
    public dialog: MatDialog
  ) {}

  ngOnInit() {
    this.incomingData$ = this.websocket_service.subscribeResultDetails(
      this.current_result.data_type,
      this.current_result.plugin_type,
      this.current_result.result_id,
      this.current_result._id
    );
    this.incomingData$.subscribe(x => this.handleIncomingData(x));
  }

  ngOnDestroy() {
    this.websocket_service.unsubscribeResultDetails(this.incomingData$);
  }

  public handleIncomingData(data: any) {
    console.log("handleIncomingData", data);

    // Set full_result to incoming data
    this.full_result = data;

    // Load default plot
    if ("results" in this.full_result) {
      if ("plots" in this.full_result.results) {
        if ("osc_range" in this.full_result.results.plots) {
          this.selected_plot = "osc_range";
          this.setPlot("osc_range");
        }
      }
    }
  }

  // Display the header information
  displayHeader(image_data) {
    console.log("displayHeader", image_data);

    let config = {
      data: {
        image_data: image_data,
        image_id: false
      }
    };

    let dialogRef = this.dialog.open(HeaderDialogComponent, config);
  }

  // Set up the plot
  setPlot(plot_key: string) {
    console.log('setPlot', plot_key, this.selected_plot);

    // Load the result for convenience
    let plot_result = this.full_result.results.plots[plot_key];
    console.log(plot_result);

    // Set the label in the UI
    this.selected_plot_label = plot_result.parameters.toplabel;

    // Certain features are consistent
    this.data.xs = plot_result.x_data;
    this.data.ys = plot_result.y_data;
    this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString =
      plot_result.parameters.ylabel;
    this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString =
      plot_result.parameters.xlabel;

    switch (plot_key) {
      // case 'background':
      //   this.data.xs = plot_result.x_data;
      //   this.data.ys = plot_result.y_data;
      //   // this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
      //   break;
      //
      // case 'exposure':
      //   this.data.ys = plot_result.y_data;
      //   this.data.xs = plot_result.x_data;
      //   // this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = plot_result.parameters.ylabel;
      //   // this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = plot_result.parameters.xlabel;
      //   // this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = undefined;
      //   break;

      case "osc_range":
      case "osc_range_anom":
        // First 5 plots, and no points
        this.data.ys = plot_result.y_data.slice(0, 5).map(function(el) {
          var o = Object.assign({}, el);
          o.pointRadius = 0;
          return o;
        });
        // axis options
        // this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString = 'Required Sweep Width';
        this.data.lineChartOptions.scales.yAxes[0].ticks.beginAtZero = true;
        // this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString = 'Starting Omega';
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = function(
          data
        ) {
          var xLabels = data.ticks;
          xLabels.forEach(function(labels, i) {
            if (i % 10 !== 0) {
              xLabels[i] = "";
            }
          });
          xLabels.push("360");
        };
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString =
          plot_result.parameters.xlabel + " (\u00B0)";
        this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString =
          plot_result.parameters.ylabel + " (\u00B0)";
        // Tooltips
        this.data.lineChartOptions.tooltips.callbacks.title = function(
          tooltipItem,
          data
        ) {
          return data.labels[tooltipItem[0].index] + "° start";
        };
        this.data.lineChartOptions.tooltips.callbacks.label = function(
          tooltipItem,
          data
        ) {
          return tooltipItem.yLabel + "° width";
        };
        break;

      case "max_delta_omega":
        // Limit to 1st 5 plots and take out the dots
        this.data.ys = plot_result.y_data.slice(0, 5).map(function(el) {
          var o = Object.assign({}, el);
          o.pointRadius = 0;
          return o;
        });
        this.data.xs = plot_result.x_data;
        // Axis options
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = function(
          data
        ) {
          var xLabels = data.ticks;
          xLabels.forEach(function(labels, i) {
            if (i % 10 !== 0) {
              xLabels[i] = "";
            }
          });
          xLabels.push("180");
        };
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString =
          plot_result.parameters.xlabel + " (\u00B0)";
        this.data.lineChartOptions.scales.yAxes[0].scaleLabel.labelString =
          plot_result.parameters.ylabel + " (\u00B0)";
        // Tooltips
        this.data.lineChartOptions.tooltips.callbacks.title = function(
          tooltipItem,
          data
        ) {
          return data.labels[tooltipItem[0].index] + "°";
        };
        this.data.lineChartOptions.tooltips.callbacks.label = function(
          tooltipItem,
          data
        ) {
          return tooltipItem.yLabel + "° width";
        };
        break;

      case "rad_damage":
        // Axis options
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = function(
          data
        ) {
          var xLabels = data.ticks;
          xLabels.forEach(function(labels, i) {
            if (i % 10 !== 0) {
              xLabels[i] = "";
            }
          });
          xLabels.push("180");
        };
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString =
          plot_result.parameters.xlabel + " (\u00B0)";
        // Tooltips
        this.data.lineChartOptions.tooltips.callbacks.title = function(
          tooltipItem,
          data
        ) {
          return data.labels[tooltipItem[0].index] + "\u00B0";
        };
        this.data.lineChartOptions.tooltips.callbacks.label = function(
          tooltipItem,
          data
        ) {
          return tooltipItem.yLabel;
        };
        break;

      case "wilson":
        // Take out the dots
        this.data.ys = plot_result.y_data.map(function(el) {
          var o = Object.assign({}, el);
          o.pointRadius = 0;
          return o;
        });
        // Axis options
        this.data.lineChartOptions.scales.xAxes[0].afterTickToLabelConversion = function(
          data
        ) {
          var xLabels = data.ticks;
          xLabels.forEach(function(labels, i) {
            xLabels[i] = Math.sqrt(1 / parseFloat(xLabels[i])).toFixed(2);
          });
        };
        this.data.lineChartOptions.scales.xAxes[0].scaleLabel.labelString =
          plot_result.parameters.xlabel + " (\u00C5)";
        // Tooltips
        this.data.lineChartOptions.tooltips.callbacks.title = function(
          tooltipItem,
          data
        ) {
          return (
            Math.sqrt(
              1 / parseFloat(data.labels[tooltipItem[0].index])
            ).toFixed(2) + "\u00C5"
          );
        };
        this.data.lineChartOptions.tooltips.callbacks.label = function(
          tooltipItem,
          data
        ) {
          return tooltipItem.yLabel;
        };
        break;

      default:
        break;
    }

    // console.log(this.data);
  }

  openReindexDialog() {
    let config = {
      // height: '600px',
      // width: '500px',
      data: this.full_result
    };

    let dialogRef = this.dialog.open(ReindexDialogComponent, config);
  }

  // Open the add to project dialog
  openProjectDialog() {
    let config = { data: this.current_result };
    let dialogRef = this.dialog.open(DialogSelectProjectComponent, config);
  }

  // Change the current result's display to 'pinned'
  pinResult(result) {
    result.display = "pinned";
    this.websocket_service.updateResult(result);
  }

  // Change the current result's display to undefined
  undefResult(result) {
    result.display = "";
    this.websocket_service.updateResult(result);
  }

  // change the current result's display status to 'junked'
  junkResult(result) {
    result.display = "junked";
    this.websocket_service.updateResult(result);
  }

  // signal upstream that a result's display status has changed

  printPage() {
    // var doc = jsPDF();
    //
    // doc.text(20, 20, 'Hello world!');
    // doc.text(20, 30, 'This is client-side Javascript, pumping out a PDF.');
    // doc.save('Test.pdf');
  }

  round_ten(value: number): number {
    return Math.round(value / 10) * 10;
  }
}
