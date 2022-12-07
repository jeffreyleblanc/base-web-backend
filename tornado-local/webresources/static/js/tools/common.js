/* Copyright Jeffrey LeBlanc */

const _base62 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
const _base62_len = _base62.length;
export function make_base62_id(length=6){
    let result = '';
    for(let i=0; i<length; i++){
        result += _base62.charAt(Math.floor(Math.random()*_base62_len));}
    return result;
}

export function utc_timestamp(){
    const now = new Date();
    return now.toISOString();
}
