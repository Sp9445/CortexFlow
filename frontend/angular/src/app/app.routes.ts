import { Routes } from '@angular/router';
import { LoginComponent, SignupComponent, DiaryListComponent, EditDiaryNoteComponent, AIChatComponent } from './components';
import { AuthGuard } from './guards/auth.guard';

export const routes: Routes = [
  { path: 'ai-chat', component: AIChatComponent, canActivate: [AuthGuard] },
  { path: 'login', component: LoginComponent },
  { path: 'signup', component: SignupComponent },
  { path: 'diary', component: DiaryListComponent, canActivate: [AuthGuard] },
  { path: 'diary/edit/:id', component: EditDiaryNoteComponent, canActivate: [AuthGuard] },
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: '**', redirectTo: '' }
];
