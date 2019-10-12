/**
 *  Pieces of the job puzzle:
 * 
 * 1. A Pipeline object represents an analytical task (implemented by one or
 *    more algorithms) that may be performed on user data.
 * 
 * 2. Each Pipeline object is in turn associated with a Form object. The Form
 *    object specifies how to solicit user input required to run the analytical
 *    task.
 * 
 * 3. The Form object contains FormGroups, each of which represents a set of
 *    related user inputs. Each FormGroup object contains FormFields, each of
 *    which represents a single user input.
 * 
 * 4. A Form object can produce a Job object. The Job object is sent to server,
 *    where it is used to invoke the analytics and where it is stored in the DB.
 * 
 * 5. A Form object can also produce a Job schema, which is pasted into the Eve
 *    configuration.
 * 
 * 6. A Form object can accept a Job object, which it will use to populate its
 *    FormFields.
 * 
 * 7. A JobTemplate represents a previously configured analysis to be used as a
 *    starting point in configuring future analyses. A JobTemplate includes a
 *    Job, which it uses as described in #6 to populate a Form.
 * 
 * 8. A JobRun represents an analysis that was run on the backend. It includes a
 *    Job, which it uses when displaying provenance information.
 */ 
export class Job {
    
    _created: string;
    _id: number;
    _updated: string;
    name: string;
    notes: string;
    pipeline: string;
    project_id: number;
    status: string;
    parameters: any;
    error: string;
    favorite: boolean;
    
    constructor(obj?: any) {
        // the ang2 book uses a "obj && obj.field || null" assignment pattern 
        // that I'm avoiding here because of falsy 0 and falsy ""
        // TODO how to DRY this up?
        Job.getFields().forEach((field: string) => {
            var value: any = null;
            if (obj && field in obj) {
                value = obj[field];
            }
            // need to cast this to :any in order to use []
            (<any>this)[field] = value;
        });
    }

    /**
     * Returns a Date object representing this object's _created string. Note
     * that in templates, especially if displaying dates for multiple jobs at
     * once, it's better to work directly with _created, because this returns a
     * different object every time, which means lots of change detection.
     */
    getCreatedDate(): Date {
        return new Date(this._created);
    }

    /**
     * Returns a pretty version of this object's pipeline and method.
     */
    getPrettyPipelineAndMethod(): string {
        let returnVal = this.pipeline.replace(/_/g, ' ');
        if (this.parameters.method) {
            returnVal += '/' + this.parameters.method;
        }
        return returnVal;
    }

    /**
     * Assign different color to a job indicator (a triangle in table)
     */
    getColor(): string {
        // seen in comp:
        //     - orange #E79038 (SSV)
        //     - green #1F977E
        //     - blue #64A2D9 (SA)
        //     - red #E05869 (SC)
        //     - lime #CACF47 (GSC)
        //     - teal #3DBFC2 (FP)
        switch(this.pipeline) {
            case 'sample_clustering':
                return '#E05869';
            case 'feature_prioritization':
                return '#3DBFC2';
            case 'gene_set_characterization':
                return '#CACF47';
            case 'spreadsheet_visualization':
                return '#E79038';
            case 'signature_analysis':
                return '#64A2D9';
        }
    }
    
    /** 
     * given the object recovered from the JSON attached to an Eve POST
     * response, merge the Eve attributes into this object
     * TODO figure out how we want to handle this across the board and
     * standardize the implementation
    */ 
    /*mergeEveAttributes(evePostResponseJson: any): void {
        this._created = evePostResponseJson._created;
        this._id = evePostResponseJson._id;
        this._updated = evePostResponseJson._updated;
    }*/

    /**
     * returns the field names for job objects
     */
    static getFields(): string[] {
        return ["_created", "_id", "_updated", "name",
                "notes", "pipeline", "project_id", "status", "parameters", "error", "favorite"];
    }
}
