/* Copyright Jeffrey LeBlanc */

import {G} from './global.js'
import DataManager from './DataManager.js'
import {EntryBrowser} from './vue/EntryBrowser.js'
import {EntryAdder} from './vue/EntryAdder.js'
import {POST_JSON} from './tools/fetch.js'

async function async_main(){
    console.log('Running Async Main!');

    // Make the data manager and global store
    G.store = Vue.reactive({
        root: '',
        ftree: []
    });
    G.data = new DataManager(G.store);

    // Create the main app
    const template = `
    <div>
        <nav>
            <div>Hello <b>{{user}}</b></div>
        </nav>
        <main>
            <entry-adder></entry-adder>
            <entry-browser :entries="entries"></entry-browser>
        </main>
    <div>`;
    G.V = Vue.createApp({
        template,
        components: { EntryAdder, EntryBrowser },
        data(){
            return this.$G.store
        },
        methods: {
            // pass
        }
    });

    // Add the global store
    G.V.config.globalProperties.$G = G;

    // Mount and export
    G.V.mount('#mount');

    // Export to window for debugging
    // window.G = G;

    const r = await POST_JSON('/api/v1/http/main',{
        stuff: 'mach-speed'
    });
    console.log('RRRR',r);
}

async_main();
