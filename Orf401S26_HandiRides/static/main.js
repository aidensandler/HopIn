function getCookie(c_name) {
    var i,x,y,ARRcookies=document.cookie.split(";");
    for (i=0;i<ARRcookies.length;i++){
        x=ARRcookies[i].substr(0,ARRcookies[i].indexOf("="));
        y=ARRcookies[i].substr(ARRcookies[i].indexOf("=")+1);
        x=x.replace(/^\s+|\s+$/g,"");
        if (x==c_name) {
            return unescape(y);
        }
    }
}
function setCookie(c_name,value,exdays) {
    var exdate=new Date();
    exdate.setDate(exdate.getDate() + exdays);
    var c_value=escape(value) + ((exdays==null) ? "" : "; expires="+
    exdate.toUTCString());
    document.cookie=c_name + "=" + c_value;
}

function checkForm() {
    const cityEl = document.querySelector('input[name="city"]');
    const stateEl = document.querySelector('select[name="state"], input[name="state"]');
    const city = (cityEl && cityEl.value ? cityEl.value.trim() : "");
    const state = (stateEl && stateEl.value ? String(stateEl.value).trim() : "");
    if (city.length === 0 && state.length === 0) {
        alert("Please enter a city and/or state before searching.");
        return false;
    }
    
    const needle = "elon musk";
    if (city.toLowerCase() === needle || state.toLowerCase() === needle) {
        alert("He's not here");
        return false;
    }
    return true;
    }

    document.addEventListener("DOMContentLoaded", () => {
        const VISITED_COOKIE = "hopin_visited";
        const visited = getCookie(VISITED_COOKIE);
        if (!visited) {
            setCookie(VISITED_COOKIE, "1", 30);
            if (window.location.pathname !== "/") {
                window.location.replace("/");
                return;
            }
        }
    })
