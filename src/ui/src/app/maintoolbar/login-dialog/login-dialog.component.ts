import { Component,
         OnInit,
         ViewContainerRef } from '@angular/core';
import { FormGroup,
         FormControl } from '@angular/forms';
import { MdDialogRef,
         MdDialog,
         MdDialogConfig } from '@angular/material';
import { Router } from '@angular/router';

import { CommunicateDialogComponent } from '../../shared/dialogs/communicate-dialog/communicate-dialog.component';
import { AuthService } from '../../shared/services/auth.service';
import { WebsocketService } from '../../shared/services/websocket.service';

@Component({
  selector: 'app-login-dialog',
  templateUrl: './login-dialog.component.html',
  styleUrls: ['./login-dialog.component.css']
})
export class LoginDialogComponent implements OnInit {

  mode: String;
  login_form: FormGroup;
  lostpass_form: FormGroup;
  submitted: boolean;
  show_request_success: boolean;
  public error_message = '';

  constructor(private auth_service: AuthService,
              private websocket_service: WebsocketService,
              private router: Router,
              public dialogRef: MdDialogRef<LoginDialogComponent>) { }

  ngOnInit() {

    this.mode = 'login';

    this.login_form = new FormGroup({
       email: new FormControl(),
       password: new FormControl()
    });

    this.lostpass_form= new FormGroup({
      email: new FormControl()
    });
  }

  onSubmitLogin() {

    var self = this;

    this.submitted = true;

    this.auth_service.login(this.login_form.value).subscribe(params => {
      // console.log('onSubmit >>', params);
      if (params.success === true) {
        // Initialize the websocket connection
        this.websocket_service.initializeWebsocket();
        // Navigate to the dashboard
        this.router.navigate(['dashboard']);
        this.mode = 'show_login_success';
        // Close dialog
        setTimeout(function() {
          self.dialogRef.close(params)
        }, 5000);
      } else {
        this.error_message = params.message;
      }
      this.submitted = false;
    });
  }

  onSubmitLostpass() {

    var self = this;

    this.submitted = true;

    this.auth_service.requestPass(this.lostpass_form.value).subscribe(params => {

      this.submitted = false;

      if (params.success === true) {
        this.mode = 'show_request_success';
        setTimeout(function() {self.dialogRef.close(undefined)}, 5000);
      } else {
        this.error_message = params.message;
      }
    });
  }

  exitLogin() {
    this.dialogRef.close(undefined);
  }

}
