import {
  Component,
  //  OnDestroy,
  OnInit,
  Input,
  Output,
  Pipe,
  PipeTransform,
  EventEmitter
} from "@angular/core";
import { ReplaySubject } from "rxjs/Rx";
import { Highlight } from "../../../shared/directives/highlight.directive";
import { WebsocketService } from "../../../shared/services/websocket.service";

@Component({
  selector: "app-mx-resultslist-panel",
  templateUrl: "./mx-resultslist-panel.component.html",
  styleUrls: ["./mx-resultslist-panel.component.css"]
})
export class MxResultslistPanelComponent implements OnInit /*, OnDestroy*/ {
  highlight_color = "white";
  message: string;

  // The currently active result
  active_result: string;

  // Arrays for holding result thumbnail data structures
  data_results: Array<any> = [];
  new_result_timeout: any;
  orphan_children: any = {};

  // Object for holding progressbar counters
  progressbar_counters: any = {};

  incomingData$: ReplaySubject<string>;

  result_types = {
    snap: "mx:index",
    sweep: "mx:integrate",
    merge: "mx:merge",
    mr: "mx:mr",
    sad: "mx:sad",
    mad: "mx:mad"
  };

  @Input() session_id: string;
  @Input() result_type: string;
  @Output() resultSelect = new EventEmitter();

  constructor(private websocket_service: WebsocketService) {}

  ngOnInit() {
    this.incomingData$ = this.websocket_service.subscribeResults(
      this.session_id
    );
    this.incomingData$.subscribe(x => this.handleIncomingData(x));
  }

  ngOnDestroy() {
    // this.websocket_service.unsubscribeResults(this.incomingData$);
    this.websocket_service.unsubscribeResults();
  }

  private handleIncomingData(data: any) {
    let self = this;

    // console.log(data);

    for (let result of data) {
      // console.log(result);

      // My kind of data
      if (
        (result.data_type + ":" + result.plugin_type).toLowerCase() ===
        this.result_types[this.result_type]
      ) {
        // console.log('Adding to', this.result_types[this.result_type], 'results');

        // Filter for age & status
        if (!result.display) {
          if (result.status > 0 && result.status < 99) {
            let result_time: any = Date.parse(result.timestamp);
            if (Date.now() - result_time > 3600000) {
              return false;
            }
          }
        }

        // Look for index of result
        var data_results_index = this.data_results.findIndex(function(elem) {
          if (elem._id === result._id) {
            return true;
          } else {
            return false;
          }
        });
        // Update
        if (data_results_index !== -1) {
          // console.log('  Updated data');
          this.data_results[data_results_index] = result;
          // Insert
        } else {
          // console.log('  New data');
          this.data_results.unshift(result);
          data_results_index = 0;
        }

        // Update parent objects
        if (result.parent_id) {
          // console.log('Have parent_id', result.parent_id);
          var parent_result = this.getResult(result.parent_id);
          if (parent_result) {
            // console.log('parent_result:', parent_result);
            // Look for index of result
            if (parent_result.children) {
              var my_index = parent_result.children.findIndex(function(elem) {
                if (elem._id === result._id) {
                  return true;
                } else {
                  return false;
                }
              });
              // Update
              // console.log('  my_index:', my_index);
              if (my_index !== -1) {
                // console.log('  Updated data');
                parent_result.children[my_index] = result;
                // Insert
              } else {
                // console.log('  New data');
                parent_result.children.unshift(result);
              }
            }
            // No parent result yet
          } else {
            // console.log('No parent_result yet');
            // Create entry for orphan child results
            if (!(result.parent_id in this.orphan_children)) {
              this.orphan_children[result.parent_id] = [];
            }
            // console.log('Add to orphan_children');
            this.orphan_children[result.parent_id].push(result);
          }

          // No parent - check for children
        } else {
          if (result._id in this.orphan_children) {
            // console.log('Adding orphan children to parent');
            this.data_results[
              data_results_index
            ].children = this.orphan_children[result._id];
            delete this.orphan_children[result._id];
          } else {
            this.data_results[data_results_index].children = [];
          }
        }
      }
    }

    if (this.new_result_timeout) {
      clearTimeout(this.new_result_timeout);
    }
    this.new_result_timeout = setTimeout(function() {
      // Sort the data array
      self.data_results.sort(function(a, b) {
        if (a.timestamp > b.timestamp) {
          return -1;
        } else if (a.timestamp < b.timestamp) {
          return 1;
        } else {
          return 0;
        }
      });
    }, 200);
  }

  private getResult(id: string) {
    return this.data_results.find(function(elem) {
      if (elem._id === id) {
        return true;
      } else {
        return false;
      }
    });
  }

  private onClick(id: string) {
    console.log("onClick", id);

    // Save the current result as the active result
    this.active_result = id;

    // Use the result to call for full results
    this.resultSelect.emit({
      value: this.getResult(id)
    });
  }
}
