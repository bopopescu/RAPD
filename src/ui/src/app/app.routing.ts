import { NgModule } from '@angular/core';
import { RouterModule, Routes }   from '@angular/router';

import { LoginGuard } from './shared/guards/login-guard';

import { AdminpanelComponent } from './adminpanel';
import { DashboardComponent } from './dashboard';
import { MxSessionpanelComponent } from './mx-sessionpanel';
import { PageNotFoundComponent } from './page-not-found/page-not-found.component';
import { ProjectspanelComponent } from './projectspanel';
import { SessionspanelComponent } from './sessionspanel';
import { TaskspanelComponent } from './taskspanel';
import { UnauthorizedpanelComponent } from './unauthorizedpanel/unauthorizedpanel.component';
import { WelcomepanelComponent } from './welcomepanel';

const appRoutes: Routes = [
  { path: 'welcome',
      component: WelcomepanelComponent },
  { path: 'admin',
      component: AdminpanelComponent,
      canActivate: [ LoginGuard ]},
  { path: 'dashboard',
      component: DashboardComponent,
      canActivate: [ LoginGuard ]},
  { path: 'sessions',
      component: SessionspanelComponent,
      canActivate: [ LoginGuard ]},
  { path: 'projects',
      component: ProjectspanelComponent,
      canActivate: [ LoginGuard ]},
  { path: 'tasks',
      component: TaskspanelComponent,
      canActivate: [ LoginGuard ]},
  { path: 'admin',
      component: AdminpanelComponent,
      canActivate: [ LoginGuard ]},
  { path: 'mx/:session_id',
      component: MxSessionpanelComponent,
      canActivate: [ LoginGuard ],
      children: []},
  { path: '',
      pathMatch: 'full',
      redirectTo: '/welcome' },
  // { path: 'project/mx/:project_id',
  //     component: MxProjectpanelComponent,
  //     canActivate: [ LoginGuard ],
  //     children: []},
  { path: 'unauthorized',
      component: UnauthorizedpanelComponent},
  { path: '**',
      component: PageNotFoundComponent },
];

export const appRoutingProviders: any[] = [

];

// export const routing = RouterModule.forRoot(appRoutes);

@NgModule({
  imports: [
    RouterModule.forRoot(
      appRoutes,
      {
        enableTracing: false,
      }
    )
  ],
  exports: [
    RouterModule
  ]
})
export class AppRoutingModule {}
