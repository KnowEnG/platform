import {Injectable} from '@angular/core';
import {LogService} from '../../services/common/LogService';

import {ErrorHandler} from "@angular/core";

@Injectable()
export class NestErrorHandler implements ErrorHandler {
  constructor(private logger: LogService) {
  }

  /**
   * Override default error handler to send errors to the logging service.
   * This will forward them to the server and echo them to the nest_flask container logs
   */
  handleError(error: any) {
      // POST the error to the server
      this.logger.error(error.message, error.stack);
  }
}

