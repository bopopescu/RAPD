import { Component, Inject, OnInit } from "@angular/core";
import { FormControl, FormGroup, Validators } from "@angular/forms";
import {
  MAT_DIALOG_DATA,
  MatDialog,
  MatDialogRef,
  MatSnackBar
} from "@angular/material";

import { DialogNewProjectComponent } from "../../../shared/components/dialog-new-project/dialog-new-project.component";
import { GlobalsService } from "../../../shared/services/globals.service";
import { RestService } from "../../../shared/services/rest.service";

@Component({
  selector: "app-sad-dialog",
  templateUrl: "./sad-dialog.component.html",
  styleUrls: ["./sad-dialog.component.css"]
})
export class SadDialogComponent implements OnInit {
  public submitted: boolean = false;
  public submitError: string = "";
  public sadForm: FormGroup;
  public disulfideDisabled = true;

  // Projects for the group that owns the session
  public projects = [];

  // Sequences for the group that owns the session
  public sequences = [];

  constructor(
    private globalsService: GlobalsService,
    private restService: RestService,
    private newProjectDialog: MatDialog,
    @Inject(MAT_DIALOG_DATA) public data: any,
    public dialogRef: MatDialogRef<SadDialogComponent>,
    public snackBar: MatSnackBar
  ) {}

  public ngOnInit() {
    // Create form
    this.sadForm = new FormGroup({
      description: new FormControl(""),
      element: new FormControl("Se"),
      hires_cutoff: new FormControl(0),
      number_atoms: new FormControl(0),
      number_disulfides: new FormControl(0),
      number_trials: new FormControl(1024),
      project: new FormControl("", Validators.required),
      sequence: new FormControl(0),
    });
    this.onChanges();

    // Get the projects for the current group
    this.getProjects(this.globalsService.currentSession);
  }

  private onChanges(): void {

    const self = this;

    this.sadForm.valueChanges.subscribe((val) => {
      console.log("onChanges", val);

      // New project
      if (val.project === -1) {
        const newProjectDialogRef = this.newProjectDialog.open(DialogNewProjectComponent);
        newProjectDialogRef.componentInstance.dialog_title = "Create New Project";
        newProjectDialogRef.afterClosed().subscribe((result) => {
          if (result) {
            if (result.success === true) {
              self.projects.push(result.project);
              self.sadForm.controls["project"].setValue(result.project._id);
            }
          } else {
            self.sadForm.controls["project"].reset();
          }
        });
      }

      // Disable/Enable the PDB select and upload based on the input
      if (val.pdb_id) {
        this.pdbSelectDisabled = true;
      } else {
        this.pdbSelectDisabled = false;
      }
  }
}

  private getProjects(session_id: string) {
    this.restService.getProjectsBySession(session_id).subscribe(parameters => {
      // console.log(parameters);
      if (parameters.success === true) {
        this.projects = parameters.result;
      }
    });
  }
}
