import { ChangeDetectorRef, Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { environment } from '../../../environments/environment';
import { AppService } from '../../app.service';
import { DiaryEntry, ErrorResponse } from '../../app.model';
import { Subscription } from 'rxjs/internal/Subscription';
import { clearAuthTokens } from '../../auth/token-storage';

@Component({
	selector: 'app-diary-list-component',
	standalone: true,
	imports: [CommonModule, FormsModule, RouterModule],
	templateUrl: './diary-list.component.html',
	styleUrls: ['./diary-list.component.css']
})
export class DiaryListComponent implements OnInit, OnDestroy {
	diaryEntries: DiaryEntry[] = [];
	errorMessage = '';
	loadingMessage = '';
	isLoading = false;
	showFilters = false;

	// Filter properties
	fromDate: string = '';
	toDate: string = '';
	searchText: string = '';

    private subscriptions: Subscription[] = [];

	constructor(private appService: AppService,
         private router: Router,
        private cd : ChangeDetectorRef) {}

	ngOnInit(): void {
		this.initDateFilters();
		this.loadEntries();
	}

	private initDateFilters(): void {
		const today = new Date();
		const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
		const lastDayOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0);

		this.fromDate = this.formatDateForInput(firstDayOfMonth);
		this.toDate = this.formatDateForInput(lastDayOfMonth);
	}

	private formatDateForInput(date: Date): string {
		const year = date.getFullYear();
		const month = String(date.getMonth() + 1).padStart(2, '0');
		const day = String(date.getDate()).padStart(2, '0');
		return `${year}-${month}-${day}`;
	}

	async loadEntries(): Promise<void> {
		this.errorMessage = '';
		this.isLoading = true;
		this.loadingMessage = 'Loading entries...';

		
        const params = new URLSearchParams();

        if (this.fromDate) {
            // Convert date string to datetime ISO format
            params.append('from_date', new Date(this.fromDate).toISOString());
        }
        if (this.toDate) {
            // Convert date string to datetime ISO format
            const toDateObj = new Date(this.toDate);
            toDateObj.setHours(23, 59, 59, 999);
            params.append('to_date', toDateObj.toISOString());
        }
        if (this.searchText.trim()) {
            params.append('search', this.searchText.trim());
        }

        const url = environment.baseUrl + '/diary/?' + params.toString();
        
        let sub = this.appService.apiCall<DiaryEntry[]>(
            'GET',
            url
        ).subscribe({
            next: (response: DiaryEntry[]) => {
                this.isLoading = false;
                this.diaryEntries = response || [];
                this.cd.detectChanges();
            },
            error: (e: any) => {
                this.isLoading = false;
                const error = e?.error as ErrorResponse;
                this.errorMessage = error?.detail || 'Failed to load entries';
                console.error('Error loading entries:', e);
                this.cd.detectChanges();
            }
        });

        this.subscriptions.push(sub);
	}

	async onSearch(): Promise<void> {
		await this.loadEntries();
		this.showFilters = false;
	}

	toggleFilters(): void {
		this.showFilters = !this.showFilters;
	}

	resetFilters(): void {
		this.searchText = '';
		this.initDateFilters();
		// this.loadEntries();
	}

	onNewNote(): void {
		this.router.navigate(['/diary/edit/0']);
	}

	onNewChat(): void {
		this.router.navigate(['/ai-chat']);
	}

	onLogout(): void {
		const sub = this.appService.apiCall<{ detail: string }>(
			'POST',
			environment.baseUrl + '/auth/logout',
			undefined,
			undefined,
			{ withCredentials: true }
		).subscribe({
			next: () => {
				clearAuthTokens();
				this.router.navigate(['/login']);
			},
			error: (e: any) => {
				console.error('Logout failed', e);
			},
		});

		this.subscriptions.push(sub);
	}

	onDeleteEntry(entry: DiaryEntry, event: MouseEvent): void {
		event.stopPropagation();

		if (!confirm('Are you sure you want to delete this note?')) {
			return;
		}

		const url = `${environment.baseUrl}/diary/${entry.id}`;
		const sub = this.appService.apiCall<void>(
			'DELETE',
			url,
			undefined,
			undefined,
			{ withCredentials: true }
		).subscribe({
			next: () => {
				this.diaryEntries = this.diaryEntries.filter((existing) => existing.id !== entry.id);
				this.cd.detectChanges();
			},
			error: (e: any) => {
				const error = e?.error as ErrorResponse;
				this.errorMessage = error?.detail || 'Failed to delete entry';
				console.error('Error deleting entry:', e);
				this.cd.detectChanges();
			},
		});

		this.subscriptions.push(sub);
	}

    onNoteClick(entry: DiaryEntry): void {
        this.router.navigate(['/diary/edit/', entry.id]);
    }

	ngOnDestroy(): void {
		this.subscriptions.forEach(sub => sub.unsubscribe());
	}

	truncateText(text: string, maxLength: number = 200): string {
		if (!text) return '';
		if (text.length <= maxLength) return text;
		return text.substring(0, maxLength) + '...';
	}

	formatDate(dateString?: string): string {
		if (!dateString) return '';
		const date = new Date(dateString);
		return date.toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}
}
