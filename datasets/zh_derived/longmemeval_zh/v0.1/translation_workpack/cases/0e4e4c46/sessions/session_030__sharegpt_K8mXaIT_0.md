---
question_id: "0e4e4c46"
session_index: 30
session_id: "sharegpt_K8mXaIT_0"
timestamp: "2023/05/24 (Wed) 09:32"
is_evidence_session: false
turn_count: 8
translation_status: TODO
---
# Session 030 Translation

> 按 turn 翻译，只编辑 `ZH_TURN_*` 边界内的内容。不要编辑 source、role、has_answer、ID 或时间。

## Turn 000 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_000_BEGIN -->
How to build bot using engati platform
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
Engati is a popular chatbot building platform that allows you to create and deploy bots across various platforms such as Facebook Messenger, WhatsApp, Slack, and many more. Here's a general guide on how to build a bot using Engati:

1. Sign up for an account on Engati website: Go to Engati website and sign up for an account. You can choose the type of account you want to sign up for, such as a free account or a paid one.
2. Create a new bot: Once you have signed up for an account, click on the "Create Bot" button on the dashboard. Give your bot a name, and select the platform you want to create the bot for. You can choose from various platforms such as Facebook, WhatsApp, Slack, and more.
3. Design the bot: Once you have selected the platform, you can start designing the bot. You can add different elements such as text, images, videos, and more to create a conversation flow for your bot.
4. Add responses: After designing the conversation flow, you can add responses to the bot for various user inputs. You can use Engati's Natural Language Processing (NLP) engine to train your bot to understand user inputs and respond accordingly.
5. Test the bot: Once you have designed and added responses to the bot, you can test it by using the "Preview" button on the dashboard. You can test the bot on various platforms and make changes as required.
6. Deploy the bot: Once you are satisfied with the bot's performance, you can deploy it on the platform you have selected. Engati makes it easy to deploy bots across various platforms, and you can do it with just a few clicks.
7. Monitor the bot: After deploying the bot, you can monitor its performance using Engati's analytics dashboard. You can track user engagement, conversation history, and more to make changes and improve the bot's performance.

That's it! These are the basic steps to build a bot using Engati. Of course, there are many advanced features and customization options available on Engati that you can explore to make your bot more powerful and efficient.
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
How can i write script node in Engati bot
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
To write a script node in Engati bot, you can follow these steps:

1. Log in to your Engati account and go to the bot builder dashboard.
2. Click on the "Add Node" button to create a new node.
3. Select "Script" as the node type from the list of available options.
4. In the script editor window that appears, you can write your Node.js code to perform the desired actions.
5. You can use Engati's built-in libraries and modules to interact with various APIs, databases, and other external services. For example, you can use the "request" module to make HTTP requests or the "mongodb" module to access a MongoDB database.
6. Once you have written the script code, click on the "Save" button to save the node.
7. You can connect the script node to other nodes in the conversation flow to create a complete chatbot experience.

Note: Engati supports Node.js version 10.x and higher. Also, you need to ensure that your code is asynchronous and doesn't block the main event loop, as this can cause performance issues with your bot.

In summary, writing a script node in Engati is a straightforward process. You can use Node.js code to perform complex actions and interact with various services to create a powerful and dynamic chatbot.
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
Example of a script node in engati bot builder?
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
Sure, here is an example of a script node in Engati bot builder:

Suppose you want to build a script node that sends a message to a user's email address. You can use the following Node.js code to accomplish this:
```javascript
const nodemailer = require('nodemailer');

const transporter = nodemailer.createTransport({
  service: 'gmail',
  auth: {
    user: 'youremail@gmail.com',
    pass: 'yourpassword'
  }
});

const mailOptions = {
  from: 'youremail@gmail.com',
  to: '{{context.userProfile.email}}',
  subject: 'Test email from Engati bot',
  text: 'This is a test email sent from Engati bot'
};

transporter.sendMail(mailOptions, function(error, info){
  if (error) {
    console.log(error);
  } else {
    console.log('Email sent: ' + info.response);
  }
});
```
In this code, we are using the `nodemailer` module to send an email to the user's email address. We create a transporter object by providing our Gmail credentials, and then we define the email message using the `mailOptions` object. Finally, we use the `sendMail()` method to send the email and log the result.

To use this code in Engati, you can create a script node and paste this code into the script editor window. You can then connect this node to other nodes in the conversation flow to trigger the email sending action.

Note that in the `mailOptions` object, we are using Engati's context variable `{{context.userProfile.email}}` to dynamically populate the user's email address. This is because Engati stores the user's email address in the `userProfile` context variable, which we can access using the double curly braces syntax.
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
Can i integrate Shopify with Engati
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
Yes, you can integrate Shopify with Engati using Engati's webhook feature. Here's a general overview of how to do it:

1. Log in to your Engati account and go to the bot builder dashboard.
2. Create a new node that triggers when a user places an order or performs an action in Shopify. You can do this by using Shopify's webhook feature to send a notification to a webhook URL that you provide.
3. In the Shopify webhook settings, specify the webhook URL as the Engati webhook URL. This URL is provided in the Engati dashboard under the "Integrations" section.
4. In the Engati webhook node, you can write Node.js code to handle the incoming webhook data and trigger a response in your bot. You can use Engati's built-in libraries and modules to interact with the Shopify API and perform various actions, such as sending a confirmation message to the user or updating the user's order status.
5. Test the webhook integration by performing an action in Shopify that triggers the webhook, such as placing an order or updating a customer record.
6. Once you have tested the webhook integration, you can deploy it to your live Shopify store and start using it to automate various tasks and interactions with your customers.

Note that the specific steps and code required for the webhook integration may vary depending on your specific use case and requirements. However, Engati provides a flexible and powerful webhook feature that allows you to easily integrate with Shopify and other external services.
<!-- SOURCE_TURN_007_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_007_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_007_END -->
