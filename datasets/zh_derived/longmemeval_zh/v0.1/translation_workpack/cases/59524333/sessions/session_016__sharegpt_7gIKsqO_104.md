---
question_id: "59524333"
session_index: 16
session_id: "sharegpt_7gIKsqO_104"
timestamp: "2023/03/15 (Wed) 12:33"
is_evidence_session: false
turn_count: 10
translation_status: TODO
---
# Session 016 Translation

> 按 turn 翻译，只编辑 `ZH_TURN_*` 边界内的内容。不要编辑 source、role、has_answer、ID 或时间。

## Turn 000 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_000_BEGIN -->
I just need the JS file
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
Here it is:
```
const buttonList = document.querySelectorAll('input[type=button]');
const telInput = document.querySelector('input[type=tel]');
telInput.tabIndex = -1;
telInput.focus();

const addClass = (className) => (el) => el.classList.add(className);
const removeClass = (className) => (el) => el.classList.remove(className);
const setValue = (el, value) => (el.value += value);

const setupButtonEventListeners = (button) => {
  button.addEventListener("mousedown", addClass("ativa"));
  button.addEventListener("mouseup", removeClass("ativa"));
  button.addEventListener("keydown", (e) => {
    if (e.key === " " || e.key === "Enter") addClass("ativa")(button);
  });
  button.addEventListener("keyup", removeClass("ativa"));
  button.addEventListener("click", () => setValue(telInput, button.value));
};

buttonList.forEach((button, index) => {
  button.tabIndex = index + 1;
  setupButtonEventListeners(button);
});

const firstButton = buttonList[0];
firstButton.addEventListener("keydown", (e) => {
  if (e.key === "Tab" && e.shiftKey) {
    e.preventDefault();
    telInput.focus();
  }
});

const setupInputEventListeners = (el) => {
  el.addEventListener("keydown", addClass("ativa"));
  el.addEventListener("keyup", removeClass("ativa"));
};
setupInputEventListeners(telInput);
```
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
Let's go back to the JS file from before. Here it is:

const buttonList = document.querySelectorAll('input[type=button]')
const telInput = document.querySelector('input[type=tel]')
telInput.tabIndex = -1
telInput.focus()

function setupButtonEventListeners(button) {
 const events = [
 {event: "mousedown", action: () => button.classList.add("ativa")},
 {event: "mouseup", action: () => button.classList.remove("ativa")},
 {event: "keydown", action: (e) => {
 if (e.key === " " || e.key === "Enter") button.classList.add("ativa")
 }},
 {event: "keyup", action: () => button.classList.remove("ativa")},
 {event: "click", action: () => telInput.value += button.value},
 ];

 events.forEach(({event, action}) => {
 button.addEventListener(event, action);
 });
}

for (let index = 0; index < buttonList.length; index++) {
 const button = buttonList[index]
 button.tabIndex = index + 1
 setupButtonEventListeners(button)
}

const firstButton = buttonList[0]
firstButton.addEventListener("keydown", e => {
 if (e.key === "Tab" && e.shiftKey) {
 e.preventDefault()
 telInput.focus()
 }
})

telInput.addEventListener("keydown", e => {
 if (e.key === " " || e.key === "Enter") telInput.classList.add("ativa")
});

telInput.addEventListener("keyup", () => telInput.classList.remove("ativa"))

How do I use a forEach method in the following lines?:

telInput.addEventListener("keydown", e => {
 if (e.key === " " || e.key === "Enter") telInput.classList.add("ativa")
});

telInput.addEventListener("keyup", () => telInput.classList.remove("ativa"))
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
You can use a forEach method by creating an array of objects that contains the event type and the action to be performed, then looping through the array and calling `addEventListener` for each event type and action.

Here is an example of how you can refactor the code to use a forEach method:
```
const telEvents = [
  {event: "keydown", action: e => {
    if (e.key === " " || e.key === "Enter") telInput.classList.add("ativa")
  }},
  {event: "keyup", action: () => telInput.classList.remove("ativa")},
];

telEvents.forEach(({event, action}) => {
    telInput.addEventListener(event, action);
});
```
You can see that I create an array called `telEvents` that contains two objects, one for each event listener. Then I use a forEach loop to go through each object in the array and add the event listener to the telInput element.
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
Wonderful! Here's the complete JS code as it stands:

const buttonList = document.querySelectorAll('input[type=button]')
const telInput = document.querySelector('input[type=tel]')
telInput.tabIndex = -1
telInput.focus()

function setupButtonEventListeners(button) {
 const events = [
 {event: "mousedown", action: () => button.classList.add("ativa")},
 {event: "mouseup", action: () => button.classList.remove("ativa")},
 {event: "keydown", action: (e) => {
 if (e.key === " " || e.key === "Enter") button.classList.add("ativa")
 }},
 {event: "keyup", action: () => button.classList.remove("ativa")},
 {event: "click", action: () => telInput.value += button.value},
 ];

 events.forEach(({event, action}) => {
 button.addEventListener(event, action);
 });
}

for (let index = 0; index < buttonList.length; index++) {
 const button = buttonList[index]
 button.tabIndex = index + 1
 setupButtonEventListeners(button)
}

const firstButton = buttonList[0]
firstButton.addEventListener("keydown", e => {
 if (e.key === "Tab" && e.shiftKey) {
 e.preventDefault()
 telInput.focus()
 }
})

const telEvents = [
 {event: "keydown", action: e => {
 if (e.key === " " || e.key === "Enter") telInput.classList.add("ativa")
 }},
 {event: "keyup", action: () => telInput.classList.remove("ativa")},
];

telEvents.forEach(({event, action}) => {
 telInput.addEventListener(event, action);
});
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
Yes, that is correct. You have used the forEach method to iterate through the `telEvents` array and attach the corresponding event and action to the `telInput` element. This makes the code more readable and maintainable.
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
So how can we further refactor the entire code to make it more readable?
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
One way to improve readability would be to extract the code that sets up the button event listeners into a separate function and then call that function for each button.
Another option would be to use a more descriptive variable name for the telEvents array, for example telInputEvents or telInputEventListeners.
You can also consider grouping the related events and actions together in a single object for each input, for example like this:
```
const telInput = {
  element: document.querySelector('input[type=tel]'),
  events: {
    keydown: e => {
      if (e.key === " " || e.key === "Enter") telInput.classList.add("ativa")
    },
    keyup: () => telInput.classList.remove("ativa"),
  }
};
```
This way it's more clear and easy to understand the relation between the input element and the events it listens to.

Another way could be creating a class for your phone input, which will help in modularizing and managing the code, also making it more readable and maintainable.

You can also use libraries to make the code more readable and maintainable.

Note that readability is a subjective concept and what works for one developer may not work for another. But these are some of the common ways to make the code more readable.
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
So what would the full code look like with this latest refactoring considered?
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
Here is one way the code could be refactored:
```
const buttonList = document.querySelectorAll('input[type=button]');
const telInput = document.querySelector('input[type=tel]');
telInput.tabIndex = -1;
telInput.focus();

const addEventListeners = (element, events) => {
    events.forEach(({event, action}) => {
        element.addEventListener(event, action);
    });
};

const buttonEvents = [
    {event: "mousedown", action: e => e.target.classList.add("ativa")},
    {event: "mouseup", action: e => e.target.classList.remove("ativa")},
    {event: "keydown", action: e => {
        if (e.key === " " || e.key === "Enter") e.target.classList.add("ativa")
    }},
    {event: "keyup", action: e => e.target.classList.remove("ativa")},
    {event: "click", action: e => telInput.value += e.target.value},
];

const telEvents = [
    {event: "keydown", action: e => {
        if (e.key === " " || e.key === "Enter") telInput.classList.add("ativa")
    }},
    {event: "keyup", action: e => telInput.classList.remove("ativa")},
];

buttonList.forEach((button, index) => {
    button.tabIndex = index + 1;
    addEventListeners(button, buttonEvents);
});

const firstButton = buttonList[0];
firstButton.addEventListener("keydown", e => {
    if (e.key === "Tab" && e.shiftKey) {
        e.preventDefault();
        telInput.focus();
    }
```
<!-- SOURCE_TURN_009_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_009_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_009_END -->
