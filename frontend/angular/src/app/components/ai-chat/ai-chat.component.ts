import { Component, OnInit, OnDestroy, ViewChild, ElementRef, ChangeDetectorRef, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { finalize, Subscription } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AppService } from '../../app.service';
import MarkdownIt from 'markdown-it';
import { AIMessage, AIMessages } from '../../app.model';
import { Router } from '@angular/router';

const INITIAL_PROMPT =
	'Hi there! Please introduce yourself and tell me how we can work together on my diary entries.';

@Component({
	selector: 'app-ai-chat',
	standalone: true,
	imports: [CommonModule, FormsModule],
	templateUrl: './ai-chat.component.html',
	styleUrls: ['./ai-chat.component.css']
})
export class AIChatComponent implements OnInit, OnDestroy {
	messages: AIMessage[] = [];
	prompt = '';
	loading = false;
	errorMessage = '';

	@ViewChild('messagesContainer')
	private messagesContainer?: ElementRef<HTMLElement>;

	private subscriptions: Subscription[] = [];
	private markdownIt = new MarkdownIt({ html: false, linkify: true, typographer: true });

	constructor(private appService: AppService,
		private sanitizer: DomSanitizer,
		private cd: ChangeDetectorRef,
		private ngZone: NgZone,
		private router: Router
	) { }

	ngOnInit(): void {
		// this.startConversation();
	}

	ngOnDestroy(): void {
		this.subscriptions.forEach((sub) => sub.unsubscribe());
	}

	submit(): void {
		const trimmed = this.prompt.trim();
		if (!trimmed || this.loading) {
			return;
		}

		const userMessage: AIMessage = { role: 'user', content: trimmed };
		this.messages = [...this.messages, userMessage];
		this.prompt = '';
		this.scrollToBottom();
		this.sendPayload(this.messages);
	}

	resetChat(): void {
		window.location.reload();
	}

	formatMessage(message: string): SafeHtml {
		const html = this.renderMarkdown(message || '');
		return this.sanitizer.bypassSecurityTrustHtml(html);
	}

	private startConversation(): void {
		const opener: AIMessage = { role: 'user', content: INITIAL_PROMPT };
		this.messages = [opener];
		this.sendPayload(this.messages);
	}

	private sendPayload(payload: AIMessage[]): void {
		this.loading = true;
		this.errorMessage = '';

		const sub = this.appService.apiCall<AIMessages>('POST', `${environment.baseUrl}/ai/answer`, { messages: payload })
			.pipe(finalize(() => {
				this.loading = false;
				this.cd.detectChanges();
				this.scrollToBottom();
			})
			).subscribe({
				next: (resp: AIMessages) => {
					this.ngZone.run(() => {
						if (resp?.messages?.length) {
							this.messages = resp.messages;
						}
						this.loading = false;
						this.scrollToBottom();
					});
				},
				error: (err) => {
					this.errorMessage = err?.error?.detail || 'Unable to reach the AI assistant';
					this.loading = false;
					this.scrollToBottom();
				}
			});

		this.subscriptions.push(sub);
	}

	private renderMarkdown(value: string): string {
		if (!value) {
			return '';
		}
		return this.markdownIt.render(value);
	}

	private scrollToBottom(): void {
		requestAnimationFrame(() => {
			const container = this.messagesContainer?.nativeElement;
			if (container) {
				container.scrollTop = container.scrollHeight;
			}
		});
	}

	goBack(): void {
		this.router.navigate(['/diary']);
	}
}
