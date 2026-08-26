---
question_id: "0e4e4c46"
session_index: 20
session_id: "sharegpt_FQi5DlJ_48"
timestamp: "2023/05/24 (Wed) 12:02"
is_evidence_session: false
turn_count: 10
translation_status: TODO
---
# Session 020 Translation

> 按 turn 翻译，只编辑 `ZH_TURN_*` 边界内的内容。不要编辑 source、role、has_answer、ID 或时间。

## Turn 000 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_000_BEGIN -->
$(document).ready(function () {
 $("#create-post-form").submit(function (e) {
 e.preventDefault();
 var dvdTitle = $("#dvdTitle").val();
 var maxPrice = $("#maxPrice").val();
 var category = $("#exampleSelect").val();

 

 if (maxPrice == "" && category == null) {

 $.ajax({
 type: "GET",
 url: "http://localhost:8081/filmtitle",
 data: {
 dvdTitle: dvdTitle,

 },
 success: function (data) {
 sessionStorage.setItem("searchResults", JSON.stringify(data));
 window.location.assign("searchResults.html");

 // Open a new page with the search results
 //window.open("results.php?data=" + data, "\_blank");
 }
 });

 }

 else {
 $.ajax({
 type: "GET",
 url: "http://localhost:8081/categoryname",
 data: {
 dvdTitle: dvdTitle,
 maxPrice: maxPrice,
 category: category
 },
 success: function (data) {
 sessionStorage.setItem("searchResults", JSON.stringify(data));
 window.location.assign("searchResults.html");

 // Open a new page with the search results
 //window.open("results.php?data=" + data, "\_blank");
 }
 });
 }
 });
 });

given the code above and the code given below
Search for DVD title:

Max Price:

Select Category

Search
How do I show an error message dvdTitle is empty and category is null?
<!-- SOURCE_TURN_000_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_000_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_000_END -->

## Turn 001 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_001_BEGIN -->
You can add a check before the AJAX call to check if the dvdTitle and category variables are empty or null. If they are, you can use JavaScript's alert() method to display an error message to the user. Here's an example of how you can do this:
```kotlin
if(dvdTitle === "" || category === null){
  alert("Please enter a DVD title and select a category");
  return;
}
```
You can add this check before the AJAX call in the submit function of the form. This will ensure that the AJAX call is not made if the dvdTitle and category fields are empty or null, and the error message will be displayed to the user.
<!-- SOURCE_TURN_001_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_001_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_001_END -->

## Turn 002 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_002_BEGIN -->
$(document).ready(function () {

 var searchResults = JSON.parse(sessionStorage.getItem("searchResults"));
 for (var i = 0; i < searchResults.length; i++) {
 var user = searchResults[i];
 var card = `
 
 <p class="card-text">` + user.title + `</p>
 </div>
 
 ` + user.release\_year + `
 </div>

 
 ` + user.rating + `
 </div>
 
 <a href="viewUsers.html?userid=` + user.userid + `&amp;ou=173398" class="btn btn-primary" class="View">View Film Details</a>
 </div>
 </div>`;
 $("#posts").append(card);

 }

 })
 

given the code above how do I make it so that when the "View Film Details" button is pressed it goes to a html file called "filmDetails.html" and passes searchResults into that page
<!-- SOURCE_TURN_002_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_002_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_002_END -->

## Turn 003 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_003_BEGIN -->
You can modify the "View Film Details" button's `href` attribute to point to the "filmDetails.html" page and pass the `searchResults` data as a query parameter.
You can do this by changing the `href` attribute value like this:
```php
<a href="filmDetails.html?searchResults=" + JSON.stringify(searchResults) + `" class="btn btn-primary" class="View">View Film Details</a>
```
In the `filmDetails.html` page, you can access the query parameter using JavaScript's `URLSearchParams` API and parse the JSON data.
```javascript
const urlParams = new URLSearchParams(window.location.search);
const searchResults = JSON.parse(urlParams.get("searchResults"));
```
You can then use the `searchResults` variable to display the details on the "filmDetails.html" page.
<!-- SOURCE_TURN_003_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_003_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_003_END -->

## Turn 004 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_004_BEGIN -->
$(document).ready(function () {

 var searchResults = JSON.parse(sessionStorage.getItem("searchResults"));
 
 for (var i = 0; i < searchResults.length; i++) {
 var user = searchResults[i];
 var card = `
 
 <p class="card-text">` + user.title + `</p>
 </div>
 
 ` + user.release\_year + `
 </div>

 
 ` + user.rating + `
 </div>
 
 <a href="filmDetails.html?searchResults=` + JSON.stringify(searchResults) + `" class="btn btn-primary" class="View">View Film Details</a>
 </div>
 </div>`;
 $("#posts").append(card);

 }

 })
 

given the code above how do I save the data stored in var user into the session storage when the "View Film Details" button is pressed and then send the data into a file called filmDetails.html
<!-- SOURCE_TURN_004_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_004_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_004_END -->

## Turn 005 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_005_BEGIN -->
You can save the data stored in `var user` into session storage by adding a click event listener to the "View Film Details" button and then calling the `sessionStorage.setItem` function with the variable `user` as the value.

For example:
```javascript
$(".View").on("click", function() {
    sessionStorage.setItem("selectedFilm", JSON.stringify(user));
});
```
Then in the filmDetails.html file, you can retrieve the data from the session storage by calling `sessionStorage.getItem("selectedFilm")` and parse it as a JSON object.
```javascript
var selectedFilm = JSON.parse(sessionStorage.getItem("selectedFilm"));
```
You can then use the variable `selectedFilm` to access the data stored in the session storage and display it on the filmDetails.html page.
<!-- SOURCE_TURN_005_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_005_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_005_END -->

## Turn 006 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_006_BEGIN -->
where do I insert this $(".View").on("click", function() {
 sessionStorage.setItem("selectedFilm", JSON.stringify(user));
});
<!-- SOURCE_TURN_006_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_006_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_006_END -->

## Turn 007 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_007_BEGIN -->
You would insert this code within the for loop where you are appending the card elements to the page. For example:
```css
for (var i = 0; i < searchResults.length; i++) {
    var user = searchResults[i];
    var card = `<div class="card" style="margin-top: 2rem;">
                    <div class="card-body">
                        <p class="card-text">` + user.title + `</p>
                    </div>
                    <div class="card-footer text-muted">
                        ` + user.release_year + `
                    </div>
                    <div class="card-footer text-muted">
                        ` + user.rating + `
                    </div>
                    <div class="card-footer text-muted">
                        <a href="filmDetails.html" class="btn btn-primary View">View Film Details</a>
                    </div>
                </div>`;
    $("#posts").append(card);
    $(".View").on("click", function() {
        sessionStorage.setItem("selectedFilm", JSON.stringify(user));
    });
}
```
This way, when the user clicks on the "View Film Details" button, the data associated with that specific button press (user) is saved to session storage so that it can be accessed on the next page (filmDetails.html).
<!-- SOURCE_TURN_007_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_007_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_007_END -->

## Turn 008 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_008_BEGIN -->
$(document).ready(function () {

 var searchResults = JSON.parse(sessionStorage.getItem("searchResults"));
 
 for (var i = 0; i < searchResults.length; i++) {
 var user = searchResults[i];
 var card = `
 
 <p class="card-text">` + user.title + `</p>
 </div>
 
 
 ` + user.release\_year + `
 </div>

 
 ` + user.rating + `
 </div>
 
 <a href="filmDetails.html" class="btn btn-primary View">View Film Details</a>
 </div>
 </div>`;
 $("#posts").append(card);
 $(".View").on("click", function() {
 console.log(user)
 sessionStorage.setItem("selectedFilm", JSON.stringify(user));
 });

 }
 
 })

 
 

given the code above why am I only getting the same index even if click the "view film details" button on another card?
<!-- SOURCE_TURN_008_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_008_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_008_END -->

## Turn 009 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_009_BEGIN -->
The reason you are getting the same index on every card is because of the way you are using the `for` loop to iterate through the `searchResults` array.
In your for loop, you define `user` as the current element in the `searchResults` array, and then you bind the click event to the `.View` class which will be present in each card.

When the loop finishes running, `user` references the last element in the `searchResults` array.

So when you click on the 'view film details' button, the event will reference the `user` variable, which is the last element in the `searchResults` array, which is the same for every card.

You can resolve this by binding the click event inside the for loop and passing the current `user` to the event.
```css
for (var i = 0; i < searchResults.length; i++) {
    var user = searchResults[i];
    var card = `<div class="card" style="margin-top: 2rem;">
                            <div class="card-body">
                                <p class="card-text">` + user.title + `</p>
                            </div>
                            <div class="card-footer text-muted">
                                ` + user.release_year + `
                            </div>
                            <div class="card-footer text-muted">
                                ` + user.rating + `
                            </div>
                            <div class="card-footer text-muted">
                                <a href="filmDetails.html" class="btn btn-primary View">View Film Details</a>
                            </div>
                        </div>`;
    $("#posts").append(card);
    $(".View").on("click", {user:user}, function(event) {
        sessionStorage.setItem("selectedFilm", JSON.stringify(event.data.user));
    });
}
```
In this way you are passing the correct `user` to the event, so that the correct data is stored in the session storage.
<!-- SOURCE_TURN_009_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_009_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_009_END -->
