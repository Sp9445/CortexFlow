import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { Subscription } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AppService } from '../../app.service';
import { LoginRequest, AuthResponse, ErrorResponse } from '../../app.model';

@Component({
	selector: 'app-login-component',
	standalone: true,
	imports: [CommonModule, FormsModule, RouterModule],
	templateUrl: './login.component.html',
	styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit, OnDestroy {
	loginFormData: LoginRequest = { username: '', password: '' };
	errorMessage = '';
	successMessage = '';

	private subscriptions: Subscription[] = [];

	constructor(private appService: AppService, private router: Router, private cd: ChangeDetectorRef) { }

	ngOnInit(): void {
		this.resetForm();
	}

	private resetForm(): void {
		this.loginFormData = { username: '', password: '' };
	}


	submit(): void {
		this.errorMessage = '';
		this.successMessage = '';

		const sub = this.appService.apiCall<AuthResponse>(
			'POST',
			environment.baseUrl + '/auth/login',
			this.loginFormData
		).subscribe({
			next: (resp: AuthResponse) => {
				// store tokens for subsequent requests
				try {
					if (resp.access_token) {
						localStorage.setItem('access_token', resp.access_token);
					}
					if (resp.refresh_token) {
						localStorage.setItem('refresh_token', resp.refresh_token);
					}
				} catch (e) {
					console.warn('Could not persist auth tokens', e);
				}

				this.successMessage = 'Login successful — redirecting...';
				this.resetForm();
				setTimeout(() => this.router.navigate(['/diary']), 900);
				this.cd.detectChanges();
			},
			error: (e: any) => {
				const error = e?.error as ErrorResponse;
				this.errorMessage = error?.detail || 'Login failed';
			}
		});

		this.subscriptions.push(sub);
	}

	ngOnDestroy(): void {
		this.subscriptions.forEach(s => s.unsubscribe());
		this.subscriptions = [];
	}
}
