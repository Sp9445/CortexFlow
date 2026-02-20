import { ChangeDetectorRef, Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { Subscription } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AppService } from '../../app.service';
import { SignupRequest, AuthResponse, ErrorResponse } from '../../app.model';

@Component({
	selector: 'app-signup-component',
	standalone: true,
	imports: [CommonModule, FormsModule, RouterModule],
	templateUrl: './signup.component.html',
	styleUrls: ['./signup.component.css']
})
export class SignupComponent implements OnInit, OnDestroy {
	signupFormData: SignupRequest = { username: '', email: '', password: '' };
	successMessage = '';
	errorMessage = '';
	subscriptions: Subscription[] = [];

	constructor(private router: Router, private appService: AppService, private cd: ChangeDetectorRef) {}

	ngOnInit(): void {
		this.resetForm();
	}

	private resetForm(): void {
		this.signupFormData = { username: '', email: '', password: '' };
	}

	private isPasswordStrong(password: string): boolean {
		return this.passwordPattern.test(password);
	}

	private passwordPattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*\W).{8,}$/;

	async submit() {
		this.successMessage = '';
		this.errorMessage = '';
		if (!this.isPasswordStrong(this.signupFormData.password)) {
			this.errorMessage =
				'Password must be at least 8 characters long and include uppercase, lowercase, numeric, and special characters.';
			return;
		}
		try {
			const sub = this.appService.apiCall<AuthResponse>(
				'POST',
				environment.baseUrl + '/auth/register',
				this.signupFormData
			).subscribe({
				next: (_resp: AuthResponse) => {
					this.successMessage = 'Account created — redirecting to login...';
					this.resetForm();
					setTimeout(() => this.router.navigate(['/login']), 900);
					this.cd.detectChanges();
				},
				error: (e: any) => {
					const error = e?.error as ErrorResponse;
					this.errorMessage = error?.detail || 'Registration failed';
					console.error('Error during registration:', e);
					this.cd.detectChanges();
				}
			});
			this.subscriptions.push(sub);

			
		} catch (e: any) {
			const error = e?.error as ErrorResponse;
			this.errorMessage = error?.detail || 'Registration failed';
		}
	}

	ngOnDestroy(): void {
		this.subscriptions.forEach(sub => sub.unsubscribe());
	}
}
