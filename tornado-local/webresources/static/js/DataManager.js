/* Copyright Jeffrey LeBlanc */

import {make_base62_id,utc_timestamp} from './tools/common.js'

export default class DataManager {

    constructor(store){
        this._store_ref = store;
        this.entry_by_id = new Map();
    }

    //-- API Interaction -------------------------------------//

        resync_vue(){
            const entries = Array.from(this.entry_by_id.values());
            entries.sort((a, b) => b.modified.localeCompare(a.modified));
            this._store_ref.entries = Object.freeze(entries);
        }

        async make_new(text){
            this.upsert_entry({
                id: make_base62_id(),
                modified: utc_timestamp(),
                text
            });
            this.resync_vue();
        }

        async delete(entry_uuid){
            this.delete_entry(entry_uuid);
            this.resync_vue();
        }

    //-- Core Object Management -------------------------------------//

        upsert_entry(e){
            this.entry_by_id.set(e.id,e);
        }

        delete_entry(entry_id){
            this.entry_by_id.delete(entry_id);
        }

}