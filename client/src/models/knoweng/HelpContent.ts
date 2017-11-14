export class HelpContent {
    constructor(
        public groups: HelpContentGroup[]) {
    }
}

export class HelpContentGroup {
    constructor(
        public text: string,
        public elements: HelpContentElement[]) {
    }
}

export class HelpContentElement {
    constructor(
        public text: string,
        public type: HelpElementType) {
    }
}

export enum HelpElementType {HEADING, BODY}
