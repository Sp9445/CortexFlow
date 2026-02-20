import { Injectable } from '@angular/core';
import { CanActivate, ActivatedRouteSnapshot, Router, RouterStateSnapshot } from '@angular/router';
import { Observable, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { AppService } from '../app.service';
import { environment } from '../../environments/environment';
import { EnvironmentInformationResponse } from '../app.model';

@Injectable({
	providedIn: 'root'
})
export class AuthGuard implements CanActivate {
	constructor(private appService: AppService, private router: Router) {}

	canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Observable<boolean> {
		return this.appService
			.apiCall<EnvironmentInformationResponse>(
				'GET',
				`${environment.baseUrl}/environment/information`,
				undefined,
				undefined,
				{ withCredentials: true }
			)
			.pipe(
				map((resp) => {
					const isAuthenticated = !!resp.user;
					if (!isAuthenticated) {
						this.router.navigate(['/login'], { queryParams: { returnUrl: state.url } });
					}
					return isAuthenticated;
				}),
				catchError(() => {
					this.router.navigate(['/login'], { queryParams: { returnUrl: state.url } });
					return of(false);
				})
			);
	}
}
