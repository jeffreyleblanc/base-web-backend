/* Copyright Jeffrey LeBlanc */

import {make_base62_id} from '../tools/common.js'

const template = `
<section>
    <h3>Add new entry</h3>
    <div>
        <label>Text</label>
        <input type="text" v-model="text"></input>
    </div><div>
        <button class="btn btn-blue" @click="add">Add</button
    </div>
</section>`;

export const EntryAdder = {
    template,
    name: 'entry-adder',
    data(){ 
        return {
            text: ''
        }
    },
    methods: {
        add(){
            let text = this.text;
            if(text==''){ text = make_base62_id(); }
            this.$G.data.make_new(text)
            this.text = '';
        }
    }
};
