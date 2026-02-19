import { Component, OnInit, OnDestroy, ChangeDetectorRef, NgZone, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule, ActivatedRoute } from '@angular/router';
import { Subscription } from 'rxjs';
import { finalize } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { AppService } from '../../app.service';
import { DiaryEntry, ErrorResponse, DiaryEntryUpdateRequest } from '../../app.model';

@Component({
	selector: 'app-edit-diary-note-component',
	standalone: true,
	imports: [CommonModule, FormsModule, RouterModule],
	templateUrl: './edit-diary-note.component.html',
	styleUrls: ['./edit-diary-note.component.css']
})
export class EditDiaryNoteComponent implements OnInit, OnDestroy {
	entryId: string = '0'; // '0' for new entry
	rawText: string = '';
	improvedText: string = '';
	isImproved: boolean = false;
	isLoading: boolean = false;
	isSaving: boolean = false;
	isImproving: boolean = false;
	errorMessage: string = '';
	successMessage: string = '';
	showImprovedView: boolean = false;

	constructor(
		private appService: AppService,
		private router: Router,
		private route: ActivatedRoute,
		private cd: ChangeDetectorRef,
		private ngZone: NgZone
	) { }

	private subscriptions: Subscription[] = [];
	@ViewChild('editorPanel') private editorPanel?: ElementRef<HTMLElement>;

	ngOnInit(): void {
		this.route.paramMap.subscribe(params => {
			this.entryId = params.get('id') || '0';
			if (this.entryId !== '0') {
				this.loadEntry();
			}
		});
	}

	private loadEntry(): void {
		this.isLoading = true;
		this.errorMessage = '';
		const url = environment.baseUrl + '/diary/' + this.entryId;
		const sub = this.appService.apiCall<DiaryEntry>('GET', url).
		subscribe({
			next: (response: DiaryEntry) => {
				this.rawText = response.raw_text;
				this.improvedText = response.improved_text || '';
				this.isImproved = response.is_improved;
				this.isLoading = false;
				this.cd.detectChanges();
			},
			error: (e: any) => {
				this.isLoading = false;
				const error = e?.error as ErrorResponse;
				this.errorMessage = error?.detail || 'Failed to load entry';
				console.error('Error loading entry:', e);
				this.cd.detectChanges();
			}
		});
		this.subscriptions.push(sub);
	}

	get canShowActions(): boolean {
		return this.rawText.length > 25;
	}

		onImprove(): void {
			this.errorMessage = '';
			this.successMessage = '';
			this.isImproving = true;
			const url = environment.baseUrl + '/ai/improve';
			const sub = this.appService.apiCall<DiaryEntryUpdateRequest>(
				'POST',
				url,
				{ raw_text: this.rawText }
			).pipe(
				finalize(() => {
					this.isImproving = false;
					this.cd.detectChanges();
				})
			).subscribe({
				next: (response: DiaryEntryUpdateRequest) => {
					console.log('Improve success', response);
				this.ngZone.run(() => {
					this.improvedText = response.improved_text || '';
					this.isImproved = response.is_improved ?? true;
					this.showImprovedView = true;
					this.successMessage = 'Text improved successfully!';
					this.cd.detectChanges();
					this.scrollEditorToBottom();
				});
			},
				error: (e: any) => {
					const error = e?.error as ErrorResponse;
					this.errorMessage = error?.detail || 'Failed to improve text';
					console.error('Error improving text:', e);
					this.cd.detectChanges();
				}
			});

			this.subscriptions.push(sub);
		}

	onEditImproved(): void {
		this.rawText = this.improvedText;
		this.showImprovedView = false;
		this.isImproved = true;
	}

	onSave(): void {
		this.errorMessage = '';
		this.successMessage = '';
		this.isSaving = true;

		const payload: DiaryEntryUpdateRequest = {
			raw_text: this.rawText,
			improved_text: this.showImprovedView ? this.improvedText : undefined,
			is_improved: this.isImproved
		};

		if (this.entryId === '0') {
			const url = environment.baseUrl + '/diary/';
			const sub = this.appService.apiCall<DiaryEntry>(
				'POST',
				url,
				{ raw_text: this.rawText }
			).subscribe({
				next: (_resp: DiaryEntry) => {
					this.successMessage = 'Entry created successfully!';
					this.isSaving = false;
					setTimeout(() => this.router.navigate(['/diary']), 900);
					this.cd.detectChanges();
				},
				error: (e: any) => {
					this.isSaving = false;
					const error = e?.error as ErrorResponse;
					this.errorMessage = error?.detail || 'Failed to save entry';
					console.error('Error saving entry:', e);
					this.cd.detectChanges();
				}
			});
			this.subscriptions.push(sub);
		} else {
			const url = environment.baseUrl + '/diary/' + this.entryId;
			const sub = this.appService.apiCall<DiaryEntry>(
				'PATCH',
				url,
				payload
			).subscribe({
				next: (_resp: DiaryEntry) => {
					this.successMessage = 'Entry saved successfully!';
					this.isSaving = false;
					setTimeout(() => this.router.navigate(['/diary']), 900);
					this.cd.detectChanges();
				},
				error: (e: any) => {
					this.isSaving = false;
					const error = e?.error as ErrorResponse;
					this.errorMessage = error?.detail || 'Failed to save entry';
					console.error('Error saving entry:', e);
					this.cd.detectChanges();
				}
			});
			this.subscriptions.push(sub);
		}
	}

	ngOnDestroy(): void {
		this.subscriptions.forEach(s => s.unsubscribe());
		this.subscriptions = [];
	}

	onBack(): void {
		this.router.navigate(['/diary']);
	}

	private scrollEditorToBottom(): void {
		requestAnimationFrame(() => {
			const container = this.editorPanel?.nativeElement;
			if (container) {
				container.scrollTop = container.scrollHeight;
			}
		});
	}

	getTextLength(): number {
		return this.rawText.length;
	}
}
