import { Routes } from '@angular/router';
import { LoginComponent, SignupComponent, DiaryListComponent, EditDiaryNoteComponent, AIChatComponent } from './components';

export const routes: Routes = [
  { path: 'ai-chat', component: AIChatComponent },
  { path: 'login', component: LoginComponent },
  { path: 'signup', component: SignupComponent },
  { path: 'diary', component: DiaryListComponent },
  { path: 'diary/edit/:id', component: EditDiaryNoteComponent },
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: '**', redirectTo: '' }
];
