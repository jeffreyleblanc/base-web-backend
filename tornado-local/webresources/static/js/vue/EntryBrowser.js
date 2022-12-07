/* Copyright Jeffrey LeBlanc */

const template = `
<section class="EntryBrowser">
    <h3>Entries</h3>
    <div>{{entries.length}}</div>
    <div 
        class="stream-entry"
        v-for="e in entries"
        :key="e.id"
    >
        <div class="txt-bold">{{e.text}}</div>
        <div class="txt-small txt-grey">{{e.id}}</div>
        <div class="txt-small txt-grey">{{e.modified}}</div>
        <button class="btn btn-red" :data-id="e.id" @click="on_delete($event)">delete</button>
    </div>
</section>`;

export const EntryBrowser = {
    template,
    name: 'entry-browser',
    props: {
        entries: Array
    },
    data(){ return {
        ask_before_delete: false
    } },
    methods: {
        on_delete(event){
            const entry_id = event.target.dataset['id']
            if( this.ask_before_delete && !window.confirm('Confirm delete?')){
                return; }
            this.$G.data.delete(entry_id);
        }
    }
};
