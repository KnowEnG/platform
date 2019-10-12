import { Component, AfterViewInit, OnChanges, Input, Directive, ElementRef } from '@angular/core';
import { Truncator } from '../../pipes/common/Truncator';


/*
 * This simple attribute directive wraps around the existing
 * Truncator pipe. It reads the inner HTML content of the
 * element on which the, determines its length, and compares
 * it to the maxLength (which defaults to 26).
 *
 * Attributes:
 *     trunctip => enable Truncate + Tooltip behavior
 *     tooltipText => the full tooltip text (will be truncated in text label, full text in tooltip)
 *     maxLength => override default maxLength
 *
 */
@Directive({ selector: '[trunctip]',
             host: {
                 // FIXME: For some reason it doesn't like ngx-bootstrap's tooltip :/
                 //'[attr.tooltip]': 'tooltipText',
                 '[attr.title]': 'tooltipText',
             },
             exportAs: 'trunctip' })
export class Trunctip implements AfterViewInit, OnChanges {
    @Input() maxLength: number = 26;
    @Input() tooltipText: string;

    private el: ElementRef;
    node: string;

    constructor(el: ElementRef, private truncator: Truncator) {
        this.el = el;
    }

    ngAfterViewInit() {
        this.updateText();
    }

    ngOnChanges() {
        this.updateText();
    }

    updateText() {
        if (this.el.nativeElement) {
            if (this.tooltipText.length > this.maxLength) {
                this.setText(this.truncate(this.tooltipText));
            } else {
                this.setText(this.tooltipText);
            }
        }
    }

    getText(): string {
        return this.el.nativeElement.innerHTML;
    }

    setText(newText: string): void {
        this.el.nativeElement.innerHTML = newText;
    }

    truncate(input: string): string {
        return this.truncator.transform(input, this.maxLength)
    }
}
