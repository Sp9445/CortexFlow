import { Component, OnInit, signal } from '@angular/core';
import { Router, RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AppService } from './app.service';
import { LoadingService } from './services/loading.service';
import { environment } from '../environments/environment';
import { AuthResponse } from './app.model';
import { persistAuthTokens } from './auth/token-storage';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, CommonModule],
  templateUrl: './app.html',
  styleUrls: ['./app.css']
})
export class App implements OnInit {
  protected readonly title = signal('angular');

  constructor(
    private appService: AppService,
    private router: Router,
    private loadingService: LoadingService
  ) {}

  get loading$() {
    return this.loadingService.loading$;
  }

  ngOnInit(): void {
    this.tryRestoreSession();
  }

  private tryRestoreSession(): void {
    this.appService
      .apiCall<AuthResponse>(
        'POST',
        `${environment.baseUrl}/auth/refresh`,
        undefined,
        undefined,
        { withCredentials: true }
      )
      .subscribe({
        next: (resp) => {
          persistAuthTokens(resp);
          if (['', '/', '/login'].includes(this.router.url)) {
            this.router.navigate(['/diary']);
          }
        },
        error: () => {
          // Ignore failures; user will land on the login page as usual
        },
      });
  }
}
