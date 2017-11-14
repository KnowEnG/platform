// Type definitions for Dropzone 4.0.1
// Project: http://www.dropzonejs.com/
// Definitions by: Natan Vivo <https://github.com/nvivo>, Andy Hawkins <https://github.com/a904guy/,http://a904guy.com/,http://www.bmbsqd.com>
// Definitions: https://github.com/borisyankov/DefinitelyTyped

/// <reference path="../jquery/jquery.d.ts"/>

interface DropzoneFile extends File {
	previewElement: HTMLElement;
	previewTemplate: HTMLElement;
	previewsContainer: HTMLElement;
	status: string;
	accepted: boolean;
}

interface DropzoneOptions {
	url?: string;
	method?: string;
	withCredentials?: boolean;
	parallelUploads?: number;
	maxFilesize?: number;
	paramName?: string;
	uploadMultiple?: boolean;
	headers?: any;
	addRemoveLinks?: boolean;
	previewsContainer?: string;
	clickable?: any;
	createImageThumbnails?: boolean;
	maxThumbnailFilesize?: number;
	thumbnailWidth?: number;
	thumbnailHeight?: number;
	maxFiles?: number;
	resize?: ( file?: any ) => any;
	init?: () => void;
	acceptedFiles?: string;
	accept?: ( file: DropzoneFile, doneCallback: ( ...args: any[] ) => void ) => void;
	autoProcessQueue?: boolean;
	previewTemplate?: string;
	forceFallback?: boolean;
	fallback?: () => void;

	// dictionary options
	dictDefaultMessage?: string;
	dictFallbackMessage?: string;
	dictFallbackText?: string;
	dictInvalidFileType?: string;
	dictFileTooBig?: string;
	dictResponseError?: string;
	dictCancelUpload?: string;
	dictCancelUploadConfirmation?: string;
	dictRemoveFile?: string;
	dictRemoveFileConfirmation?: string;
	dictMaxFilesExceeded?: string;
}

declare class Dropzone {
	constructor( container: string, options?: DropzoneOptions );
	constructor( container: HTMLElement, options?: DropzoneOptions );

	static autoDiscover: boolean;
	static options: any;
	static confirm: ( question: string, accepted: () => void, rejected?: () => void ) => void;

	files: DropzoneFile[];

	enable(): void;
	disable(): void;
	destroy(): Dropzone;

	on( eventName: any, callback: ( ...args: any[] ) => any ): any;

	off( eventName: any ): void;

	addFile( file: DropzoneFile ): void;

	removeFile( file: DropzoneFile ): void;

	removeAllFiles( cancelIfNecessary?: boolean ): void;

	processQueue(): void;

	cancelUpload( file: DropzoneFile ): void;

	processFiles ( files: DropzoneFile[] ): void;
	processFile( file: DropzoneFile ): void;

	uploadFile( file: DropzoneFile ): void;

	getAcceptedFiles(): DropzoneFile[];

	getRejectedFiles(): DropzoneFile[];

	getQueuedFiles(): DropzoneFile[];

	getUploadingFiles(): DropzoneFile[];

	accept( file: DropzoneFile, done: ( error?: string ) => {} ):void;
	getActiveFiles(): DropzoneFile[];
	getFilesWithStatus( status: string ): DropzoneFile[];
	enqueueFile( file: DropzoneFile ): void;
	enqueueFiles( file: DropzoneFile[] ): void;
	createThumbnail( file: DropzoneFile, callback?: (...any: any[]) => {}): any;
	createThumbnailFromUrl( file: DropzoneFile, url: string, callback?: ( ...any: any[] ) => any ): any;

	emit( eventName: string, file: DropzoneFile, str?: string ): any;
	emit( eventName: "thumbnail", file: DropzoneFile, path: string ): any;
	emit( eventName: "addedfile", file: DropzoneFile ): any;
	emit( eventName: "removedfile", file: DropzoneFile ): any;
	emit( eventName: "processing", file: DropzoneFile ): any;
	emit( eventName: "canceled", file: DropzoneFile ): any;
	emit( eventName: "complete", file: DropzoneFile ): any;

	emit( eventName: string, e: Event ): any;
	emit( eventName: "drop", e: Event ): any;
	emit( eventName: "dragstart", e: Event ): any;
	emit( eventName: "dragend", e: Event ): any;
	emit( eventName: "dragenter", e: Event ): any;
	emit( eventName: "dragover", e: Event ): any;
	emit( eventName: "dragleave", e: Event ): any;
}

interface JQuery {
	dropzone( options: DropzoneOptions ): Dropzone;
}

declare module "dropzone" {
	export = Dropzone;
}
