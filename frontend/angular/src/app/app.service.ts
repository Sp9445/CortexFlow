import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { finalize } from 'rxjs/operators';
import { LoadingService } from './services/loading.service';

interface ApiCallOptions {
  withCredentials?: boolean;
  skipLoader?: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class AppService {
  constructor(private http: HttpClient, private loadingService: LoadingService) {}

  /**
   * Common method to make HTTP requests
   * @param method HTTP method (GET, POST, PUT, PATCH, DELETE)
   * @param endpoint API endpoint URL
   * @param data Request body data (optional)
   * @param headers Custom headers (optional)
   * @returns Observable with the API response
   */
  apiCall<T>(
    method: string,
    endpoint: string,
    data?: any,
    headers?: HttpHeaders,
    options?: ApiCallOptions
  ): Observable<T> {
    let response$: Observable<T>;

    // ensure headers exists
    if (!headers) {
      headers = new HttpHeaders();
    }

    // attach Authorization header automatically when access token is present
    try {
      const token = localStorage.getItem('access_token');
      if (token && !headers.has('Authorization')) {
        headers = headers.set('Authorization', `Bearer ${token}`);
      }
    } catch (e) {
      // ignore localStorage errors in non-browser environments
    }

    const httpOptions: { headers: HttpHeaders; withCredentials?: boolean } = {
      headers,
    };

    if (options?.withCredentials) {
      httpOptions.withCredentials = true;
    }

    const shouldSkipLoader =
      options?.skipLoader ?? endpoint.toLowerCase().includes('/ai/answer');

    switch (method.toUpperCase()) {
      case 'GET':
        response$ = this.http.get<T>(endpoint, httpOptions);
        break;
      case 'POST':
        response$ = this.http.post<T>(endpoint, data, httpOptions);
        break;
      case 'PUT':
        response$ = this.http.put<T>(endpoint, data, httpOptions);
        break;
      case 'PATCH':
        response$ = this.http.patch<T>(endpoint, data, httpOptions);
        break;
      case 'DELETE':
        response$ = this.http.delete<T>(endpoint, httpOptions);
        break;
      default:
        throw new Error(`Unsupported HTTP method: ${method}`);
    }

    if (shouldSkipLoader) {
      return response$;
    }

    this.loadingService.show();
    return response$.pipe(finalize(() => this.loadingService.hide()));
  }
}
