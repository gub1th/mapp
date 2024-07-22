"use strict"



function getCSRFToken() {
    let cookies = document.cookie.split(";")
    for (let i = 0; i < cookies.length; i++) {
        let c = cookies[i].trim()
        if (c.startsWith("csrftoken=")) {
            return c.substring("csrftoken=".length, c.length)
        }
    }
    return "unknown"
}


function addComment(postId, stream) {
    //alert(postId)
    let newCommentTextElement = document.getElementById("id_comment_input_text_" + postId)
    let newCommentTextValue = newCommentTextElement.value

    newCommentTextElement.value = ''
    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function() {
        if (xhr.readyState !== 4) return
        updatePage(xhr, stream)
    }
    xhr.open("POST", addCommentURL, true)
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded")

    xhr.send(`stream=${stream}&comment_text=${newCommentTextValue}&post_id=${postId}&csrfmiddlewaretoken=${getCSRFToken()}`)
}


function addPost() {
    let newPostTextElement = document.getElementById("id_post_input_text")
    let newPostTextValue = newPostTextElement.value

    newPostTextElement.value = ''
    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function() {
        if (xhr.readyState !== 4) return
        updatePage(xhr, 0)
    }
    xhr.open("POST", addPostURL, true)
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    xhr.send(`new_post_text=${newPostTextValue}&csrfmiddlewaretoken=${getCSRFToken()}`)
}

function getFollower() {
    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function() {
        if (this.readyState !== 4) return
        updatePage(xhr, 1)
    }

    xhr.open("GET", "socialnetwork/get-follower", true)
    xhr.send(`csrfmiddlewaretoken=${getCSRFToken()}`)
}

function getGlobal() {
    let xhr = new XMLHttpRequest()
    xhr.onreadystatechange = function() {
        if (this.readyState !== 4) return
        updatePage(xhr, 0)
    }

    xhr.open("GET", "socialnetwork/get-global", true)
    xhr.send(`csrfmiddlewaretoken=${getCSRFToken()}`)
}

function updatePage(xhr, stream) {
    if (xhr.status === 200) {
        let response = JSON.parse(xhr.responseText)
        updateStream(response, stream)
        return
    }

    if (xhr.status === 0) {
        displayError("Cannot connect to server")
        return
    }


    if (!xhr.getResponseHeader('content-type') === 'application/json') {
        //displayError(`Received status = ${xhr.status}`)
        return
    }

    let response = JSON.parse(xhr.responseText)
    if (response.hasOwnProperty('error')) {
        //displayError(response.error)
        return
    }

    //displayError(response)
}



function updateStream(response, stream) {
    let list = document.getElementById("stream_list")
    let j = 0

    //find the last updated post
    for (let i = 0; i < response.posts.length; i++){
        let list_item = document.getElementById("id_list_element_"+response.posts[i].id)
        if (list_item != null) {
            break
        }
        j++;
    }

    //update new posts
    for (let i = j - 1; i >= 0; i--) {
        list.prepend(makePostListElement(response.posts[i], stream))
        //alert(response.posts[i].id)
    }

    //update comment
    for (let i = 0; i < response.comments.length; i++) {
        //skip exist comment
        if (document.getElementById("id_comment_div_"+response.comments[i].id) != null) {
            continue
        }
        let postDiv = document.getElementById("id_post_div_"+response.comments[i].for_post)
        //skip not follower post
        if (postDiv == null) {
            continue
        }
        //alert("creating comment"+response.comments[i].id)
        postDiv.append(makeCommentElement(response.comments[i]))
    }


/*
    //alert("list length:" + list.childNodes.length)
    if (list.childNodes.length == 0){
        //alert(list.childNodes[0])
        for (let i =0;i<posts.length;i++) {
            list.append(makeListItemElement(posts[i]))
        }
    } else {
        while(posts[j].post_id != list.childNodes[0].id.substring(16)){
            j++
            //alert(posts[j].post_id)
        }
        for (let i = j - 1; i >=0; i--){
            list.prepend(makeListItemElement(posts[i]))
        }

        for (let i = j; i < list.childNodes.length; i++){
            for (let k = 0; k < posts[i].comments_list.length; k++){
                //alert(list.childNodes[i].)
            }
        }

    }
*/
    
    // TODO: change different
    //while (list.hasChildNodes()) {
     //   list.firstChild.remove()
    //}

    // Adds each to do list item received from the server to the displayed list
    //posts.forEach(post => list.append(makeListItemElement(post)))
}



function makePostListElement(post,stream) {
    let listElement = document.createElement("li")
    listElement.id = `id_list_element_${post.id}`
    
    let profileHerf =`<a href="profile?profile_id=${post.post_by}" id ="id_post_profile_${post.id}">${post.firstname} ${post.lastname}</a>`
    let postTextSpan = `<span class = "post_text" id = "id_post_text_${post.id}">${post.post_text}</span>`
    let postTimeSpan = `<span class = "post_date_time" id = "id_post_date_time_${post.id}">${post.creation_time}</span>`

    listElement.innerHTML = `<div class = "post_div" id = "id_post_div_${post.id}">${profileHerf} : ${postTextSpan} ${postTimeSpan}</div>`
    let newCommentDiv = `<div class = "new_comment_div"> <label for="id_comment_input_text_${post.id}">New Comment: </label> <input id="id_comment_input_text_${post.id}" type="text" name="item">  <button id="id_comment_button_${post.id}" onclick="addComment(${post.id},${stream})">Submit</button></div>`
    listElement.innerHTML = listElement.innerHTML + newCommentDiv
    return listElement
}


function makeCommentElement(comment) {
    let commentElement = document.createElement("div")
    commentElement.id = `id_comment_div_${comment.id}`
    commentElement.className = 'comment_div'
    let commentProfileHerf = `<a href="profile?profile_id=${comment.created_by}" id ="id_comment_profile_${comment.id}">${comment.firstname} ${comment.lastname}</a>`
    let commentTextSpan = `<span class = "comment_text" id = "id_comment_text_${comment.id}">${comment.comment_text}</span>`
    let commentTimeSpan = `<span class = "post_date_time" id = "id_comment_date_time_${comment.id}">${comment.creation_time}</span>`
    commentElement.innerHTML = `${commentProfileHerf} : ${commentTextSpan} ${commentTimeSpan}`
    return commentElement
}



/*

function makeListItemElement(item) {
    let listElement = document.createElement("li")
    listElement.id = `id_list_element_${item.post_id}`
    
    let profileHerf =`<a href="profile?profile_id=${item.post_by}" id ="id_post_profile_${item.post_by}">${item.firstname} ${item.lastname}</a>`
    let postTextSpan = `<span class = "post_text" id = "id_post_text_${item.post_id}">${item.post_text}</span>`
    //let dateSpan = '<span class = "post_date_time" id = "id_post_date_time_{{post.id}}">{{post.creation_time|date:"n/j/Y g:i A"}}</span>'

    listElement.innerHTML = `<div class = "post_div" id = "id_post_div_${item.post_by}">${profileHerf} : ${postTextSpan}</div>`
    
    let newCommentDiv = `<div id = "new_comment_div"> <label for="id_comment_input_text_${item.post_id}">New Comment: </label> <input id="id_comment_input_text_${item.post_id}" type="text" name="item">  <button id="id_comment_button_${item.post_id}" onclick="addComment(${item.post_id})">Submit</button></div>`



    
    let commentsList = item.comments_list
    
    for (var i = 0; i < commentsList.length; i++){
        let commentProfileHerf =`<a href="profile?profile_id=${item.post_by}" id ="id_post_profile_${commentsList[i].created_by}">${commentsList[i].firstname} ${commentsList[i].lastname}</a>`
        let postTextSpan = `<span class = "comment_text" id = "id_comment_text_${commentsList[i].comment_id}">${commentsList[i].comment_text}</span>`
        listElement.innerHTML = listElement.innerHTML + `<div class = "comment_div" id = "id_comment_div_${commentsList[i].created_by}">${commentProfileHerf} : ${postTextSpan}</div>`
    }

    listElement.innerHTML = listElement.innerHTML + newCommentDiv

 
 


    //alert(listElement)
    return listElement
}
*/