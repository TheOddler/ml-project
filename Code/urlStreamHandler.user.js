// ==UserScript==
// @name        URL Stream Handler
// @namespace   be.kuleuven.cs.dtai
// @description Send visited urls to local server and show most likely links.
// @version     1
// @grant       GM_xmlhttpRequest
// @run-at      document-end
// ==/UserScript==

try {
  var toppage = (window.top == window.self);
  if (!toppage) {
    return;
  }

  var url = window.location.href;

  var send = function(data, onload) {
    data.ts = (new Date()).toISOString();
    data_string = JSON.stringify(data);
    GM_xmlhttpRequest({
      method: "POST",
      url: "http://localhost:8000",
      data: data_string,
      headers: {
        "Content-Type": "application/json",
        "Content-Length": data.length
      },
      onerror: function(error) {
        console.log('Calling urlStreamHandler failed', error);
      },
      onload: onload
    });
  };

  // Associate a click event with all links
  var addClickEvent = function(element) {
    if (element.dataset.dtaitracked) {
      return;
    }
    element.dataset.dtaitracked = true;
    element.addEventListener('click', function(link) {return function(event) {
      try {
        var href = '';
        if (link.href !== undefined) {
          href = link.href;
        }
        send({
          "action": "click",
          "target": href,
          "url": url,
        });
      } catch (e) {
        console.log('An error occured in a click listener', e);
      }
    };}(element));
  };
  for (var i=0; i<document.links.length; i++) {
    addClickEvent(document.links[i]);
  }
  var observer = new MutationObserver(function(mutations) {
    try {
      mutations.forEach(function(mutation) {
        try {
          var node;
          for (var i=0; i<mutation.addedNodes.length; i++) {
            node = mutation.addedNodes[i];
            if (node.tagName === "A" || node.tagName === "a") {
              addClickEvent(node);
            } else if (node.getElementsByTagName) {
              var atags = node.getElementsByTagName('a');
              for (var aidx=0; aidx<atags.length; aidx++) {
                addClickEvent(atags[aidx]);
              }
            }
          }
        } catch (e) {
          console.log('An error occured processing added nodes', e);
        }
      });
    } catch (e) {
      console.log('An error occured after a mutation change', e);
    }
  });
  observer.observe(document.body, {childList:true, subtree:true});


  // Window events
  // Possible events include hashchange, pageshow, popstate, beforeunload
  window.addEventListener('beforeunload', function(event) {
    send({
      "action": 'beforeunload',
      "url": url
    });
  });

  // Catch any other changes by polling the location
  setInterval(function() {
    try {
      if(location.href !== url) {
        send({
          "action": 'polling',
          "url": location.href,
        });
        url = location.href;
      }
    } catch (e) {
      console.log('An error occured while processing polled change', e);
    }
  }, 500);

  // Send current page load and react to result
  var html = '';
  if (document.body) {
    html = document.body.innerHTML;
  }
  send({
    "action": "load",
    "url": url,
    "top": toppage,
    "html": html
  }, function(response) {
    try {
        data = JSON.parse(response.response);
        // TODO: Do something (e.g. show a top bar with the final link of the
        //       suspected sequence)
        var best_guess = data.guesses[0][0];

        var guesses_div = document.createElement("div");
        guesses_div.style.position = "fixed";
        guesses_div.style.right = "0";
        guesses_div.style.bottom = "0";
        guesses_div.style.backgroundColor = "rgb(255, 255, 0)";
        guesses_div.style.zIndex = "100000";
        guesses_div.style.fontSize = "16px";
        for (var i=0; i < data.guesses.length; ++i) {
            var guess_link = document.createElement('a');
            guess_link.href = data.guesses[i][0];
            var title = "" + data.guesses[i][1] + ": " + data.guesses[i][0]
            guess_link.title = title;
            guess_link.appendChild(document.createTextNode(title));

            var guess_div = document.createElement('div');
            guess_div.appendChild(guess_link);
            guesses_div.appendChild(guess_div);
        }
        document.body.appendChild(guesses_div);
        console.log('Successfully processed the guesses');
    } catch (e) {
      console.log('An error occured while processing the guesses', e);
    }
  });
} catch (e) {
  console.log('An error occured', e);
}
