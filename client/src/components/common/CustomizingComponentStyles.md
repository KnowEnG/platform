Customizing Component Styles
============================

Suppose we've built an Angular 2 component we'd like to reuse, but the original use and the new use call for different styling. This document considers how we might solve that problem.

Use Cases
---------

  1. **Multi-Project.** For example, the ThresholdPicker appears in both the KnowEnG project and the OmiX project. Each project has its own styles.
  2. **Single-Project.** For example, the Tabset might appear in multiple places within the OmiX project, and each place may require its own styles.

Options
-------

Internet searches for best practices for Angular 2 didn't turn up much. Just a week ago, someone did post [a question on the subject to Stack Overflow](http://stackoverflow.com/questions/36516198/same-component-different-styles/36516274#36516274), so we'll want to keep an eye on the responses. In the meantime, the following look like reasonable options:

1. **Each component defines its own default styles using `styles` and `styleUrls`. Styles can be overridden as necessary with additional rules defined in css files loaded from the app's index page.** For example, let's say `src/components/common/ThresholdPicker.ts` has `styleUrls: ['components/common/ThresholdPicker.css']`. Let's also say `index.knoweng.html` loads `src/css/styles.css`. In that case, `src/css/styles.css` can override rules found in `components/common/ThresholdPicker.css`.
    - *Pros*:
        - The concept is simple.
        - No new gulp logic is needed.
        - It's unlikely to be affected by any future changes to Angular 2. On the other hand, I'll have to do more reading to see whether it'd cause problems with web workers or the shadow DOM.
        - It's relatively DRY.
        - The dist directory for a given project doesn't include CSS files from other projects.
    - *Cons*:
        - Encapsulation is poor. We might encounter conflicts with other DOM elements.
        - Rules in index-loaded CSS files might be difficult to maintain across projects as the underlying component evolves. Naming conventions could help.
        - Selectors might long and possibly brittle for the "single-project" case described above.
        - If we ever want to customize `template` and `templateUrls`, too, we'll need a separate approach.
    - *Conclusion*: Poor encapsulation and difficulty of maintenance seem like dealbreakers.
2. **Each component defines its own default styles using `styles` and `styleUrls`. Any project-specific CSS files to override the default styles will be moved into place by gulp's `dist` task.** For example, let's say `src/components/common/ThresholdPicker.ts` has `styleUrls: ['components/common/ThresholdPicker.css', 'css/custom/ThresholdPicker.css']`. Let's also say we have defined separate styles for KnowEnG in a designated location (e.g., `css/knoweng/ThresholdPicker.css`). When we build the KnowEnG project, gulp will copy our KnowEnG-specific file to `css/custom/ThresholdPicker.css`.
    - *Pros*:
        - The dist directory for a given project doesn't include CSS files from other projects.
        - When the underlying component evolves, finding references across projects is relatively straightforward.
        - The approach could be extended to customize `template` and `templateUrls`, too.
    - *Cons*:
        - This approach alone does not address the "single-project" case described above.
        - New gulp logic is required.
        - When reading code, one has to recognize that the paths in `styleUrls` refer to the `dist` directory and will not match the `src` directory. At some point, that might cause problems for tools (e.g., IDEs).
    - *Conclusion*: This doesn't address the "single-project" case, but it could be used in combination with option 3, which can address the "single-project" case. Option 4 will describe the combination of option 2 with option 3.
3. **Each component defines its own default *and custom* styles using `styles` and `styleUrls` with `host-context` selectors where needed.** The Stack Overflow thread mentioned above includes an example:
    ```
    :host-context(.class1) {
      background-color: red;
    }
    :host-context(.class2) {
      background-color: blue;
    }
    <my-comp class="class1"></my-comp> <!-- should be red -->
    <my-comp class="class2"></my-comp> <!-- should be blue -->
    ```
    - *Pros*:
        - When the underlying component evolves, finding references across projects is straightforward.
        - The concept is simple.
        - No new gulp logic is needed.
        - It's unlikely to be affected by any future changes to Angular 2.
        - It's relatively DRY.
    - *Cons*:
        - In the "multi-project" case described above, the `dist` directory for a given project will include style rules for other projects.
        - If we ever want to customize `template` and `templateUrls`, too, we'll need a separate approach.
    - *Conclusion*: The "multi-project" case is messy. See option 4 for an alternative that uses `host-context` selectors but doesn't have the "multi-project" problem.
4. **Combine options 3 and 4, using project-specific CSS files for "multi-project" customization and `host-context` selectors for "single-project" customization.**
    - *Pros*:
        - When the underlying component evolves, finding references across projects is relatively straightforward.
        - It's relatively DRY.
        - The dist directory for a given project doesn't include CSS files from other projects.
        - The approach could be extended to customize `template` and `templateUrls`, too.
    - *Cons*:
        - The concept is more complicated than the others.
        - New gulp logic is needed.
        - When reading code, one has to recognize that the paths in `styleUrls` refer to the `dist` directory and will not match the `src` directory. At some point, that might cause problems for tools (e.g., IDEs).
    - *Conclusion*: This option is the most complicated but seems to solve all of the problems.
5. **Each component defines its own default styles using `styles` and `styleUrls`. Custom styles are achieved by subclassing the component and redefining the `@Component` block.**
    - *Pros*:
        - Encapsulation is good.
        - When the underlying component evolves, finding references across projects is relatively straightforward. On the other hand, see the DRY comment in the *Cons* section.
        - The dist directory for a given project doesn't include CSS files from other projects.
        - The approach could be extended to customize `template` and `templateUrls`, too.
        - The concept is relatively simple.
        - No new gulp logic is needed.
    - *Cons*:
        - It's not DRY. Code from the `@Component` block that *isn't* being customized also has to be copied to the subclass.
        - Subclassing Angular 2 components isn't well documented, as far as I can see. I don't know whether the process or its consequences are likely to change, and if they do change, whether they'll become better suited for our purposes or completely eliminate this option.
    - *Conclusion*: Like option 4, this one seems to solve all of the problems. It's simpler but requires duplicating portions of `@Component` blocks that aren't related to styles or templates.


