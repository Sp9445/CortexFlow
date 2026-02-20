import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class LoadingService {
  private activeRequests = 0;
  private readonly loadingSubject = new BehaviorSubject(false);

  get loading$(): Observable<boolean> {
    return this.loadingSubject.asObservable();
  }

  show(): void {
    this.activeRequests += 1;
    if (this.activeRequests === 1) {
      this.loadingSubject.next(true);
    }
  }

  hide(): void {
    if (this.activeRequests === 0) {
      return;
    }

    this.activeRequests -= 1;
    if (this.activeRequests === 0) {
      this.loadingSubject.next(false);
    }
  }
}
