---
question_id: "d596882b"
session_index: 32
session_id: "sharegpt_WbCGgx9_0"
timestamp: "2023/05/28 (Sun) 10:00"
is_evidence_session: false
turn_count: 12
translation_status: TODO
---
# Session 032 Translation

> 按 turn 翻译，只编辑 `ZH_TURN_*` 边界内的内容。不要编辑 source、role、has_answer、ID 或时间。

## Turn 000 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_000_BEGIN -->
I'm integrating Stripe into my web app's server. I want to add an integration for using Stripe Connect with Express. My server is written in Go, can you help me set up the client I need to create accounts for users and upload their information to Stripe?
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
Stripe has an official Go library for interacting with the Stripe API, which you can use to create Stripe Connect accounts for your users and upload their information to Stripe. Here is an example of how to use the library to create a Stripe Connect account for a user:
```
package main

import (
	"fmt"
	"os"

	"github.com/stripe/stripe-go"
	"github.com/stripe/stripe-go/account"
)

func main() {
	stripe.Key = os.Getenv("STRIPE_SECRET_KEY")

	params := &stripe.AccountParams{
		Type: stripe.String(string(stripe.AccountTypeCustom)),
	}
	params.SetCountry("US")
	params.SetEmail("jane.doe@example.com")

	account, err := account.New(params)
	if err != nil {
		fmt.Println("Error creating account:", err)
		return
	}

	fmt.Println("Account ID:", account.ID)
}
```
You need to set `stripe.Key` to your Stripe Secret Key.

You may also need to pass additional information such as the user's name, address, and business information depending on the requirements for the type of account you want to create. You can find more information on the available fields in the Stripe API documentation: <https://stripe.com/docs/api/go#create_account>

You can also refer to Stripe's official Go library documentation for more information on how to use the library to interact with the Stripe API: <https://godoc.org/github.com/stripe/stripe-go>
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
When would I use Stripe's go client ("github.com/stripe/stripe-go/client")?
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
The `github.com/stripe/stripe-go/client` package provides a client that you can use to interact with the Stripe API directly. This package is lower level than some of the other packages in the Stripe Go library, and it provides more flexibility in terms of the requests you can make to the Stripe API.

You might use `github.com/stripe/stripe-go/client` if you need to perform an action that is not currently supported by the higher level packages in the Stripe Go library, or if you want more control over the requests being sent to the Stripe API.

For example, you might use the `client` package to make a custom request to the Stripe API that is not currently supported by one of the other packages. Or you might use it to configure the client with custom options such as timeouts, retry logic, or custom headers.

In general, if you're looking for an easy way to perform common Stripe operations in your Go server, you should use the higher level packages like `account`, `charge`, `customer` etc. But if you need more control over the requests being sent to the Stripe API, the `client` package might be the right choice for you.
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
Can you explain to me what an Account Link is in Stripe and why I would want to use it when using Stripe Connect with Express?
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
An Account Link is a feature provided by Stripe Connect that allows you to create a link that a user can follow to connect their Stripe account to your platform. When the user clicks on the link, they will be taken to a Stripe-hosted page where they can sign in to their existing Stripe account or create a new one. Once they have connected their account, they will be redirected back to your platform, and you will be able to access the account's details and perform actions on it.

You might want to use an Account Link when using Stripe Connect with Express because it provides a convenient and secure way for your users to connect their Stripe accounts to your platform without having to share their sensitive Stripe credentials with you. The user's Stripe account information is not accessible by you, but only by the user who created the account.

An Account Link is particularly useful when you are building a marketplace or platform that allows users to connect their Stripe accounts, for example, so that you can charge them for fees or payouts. It also provides a way for you to onboard and manage multiple users as well as their payments.

You can create an Account Link in Stripe by generating a link token with the `account_links.create` API call, and then sending it to your user. The user can then follow the link to connect their Stripe account to your platform.
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
How can I add a capability to a Stripe Account for U.S. tax reporting?
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
To add a capability for U.S. tax reporting to a Stripe Account, you can use the `capabilities.create` API call and set the `capability` parameter to `tax_reporting_us_1099_k`. This will allow the account to have the capability for U.S. tax reporting.

Here is an example of how to add a capability for U.S. tax reporting to a Stripe account using the Stripe Go library:
```
package main

import (
	"fmt"
	"os"

	"github.com/stripe/stripe-go"
	"github.com/stripe/stripe-go/capability"
)

func main() {
	stripe.Key = os.Getenv("STRIPE_SECRET_KEY")
	accountId := "acct_123"

	params := &stripe.CapabilityParams{
		Account: stripe.String(accountId),
		Capability: stripe.String("tax_reporting_us_1099_k"),
	}

	capability, err := capability.New(params)
	if err != nil {
		fmt.Println("Error adding capability:", err)
		return
	}

	fmt.Println("Capability ID:", capability.ID)
}
```
Note that you will need to set `stripe.Key` to your Stripe Secret Key and replace `acct_123` with the actual account ID for which you want to add the capability.

You can find more information on the available capabilities and how to use them in the Stripe API documentation: <https://stripe.com/docs/api/go#create_capability>

Also, note that adding this capability to an account does not automatically enable the tax reporting feature, it just gives the account the capability to do so. To enable tax reporting, you should check the Stripe documentation on how to enable the feature, as it can vary depending on the country and region.
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
What is the difference between Stripe's tax reporting US 1099 K and MISC?
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
The difference between Stripe's tax reporting US 1099-K and 1099-MISC is that they are two different forms that the IRS (Internal Revenue Service) requires to report different types of income.

* The 1099-K form is used to report payment card and third-party network transactions. It is used to report transactions processed through payment card networks such as Visa, Mastercard, and American Express, as well as transactions processed through third-party networks such as PayPal. The form is used to report gross payment card and third-party network transactions to the IRS, and it is typically required for businesses that have processed more than $20,000 in gross payments and have more than 200 transactions in a calendar year.
* The 1099-MISC form is used to report miscellaneous income, such as rent, prizes, and awards, and it is typically required for businesses that have paid out more than $600 to a non-employee in a calendar year.

Both forms are used by the IRS to track income and ensure that it is reported and taxed properly. The 1099-K form is specifically used to track income from payment card and third-party network transactions, while the 1099-MISC form is used to track miscellaneous income.

When using Stripe, businesses that use Stripe Connect to process payments will be able to generate 1099-K forms for their connected accounts, and businesses that use Stripe to pay out to vendors or independent contractors will be able to generate 1099-MISC forms.
<!-- SOURCE_TURN_009_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_009_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_009_END -->

## Turn 010 — user

- role: `user` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_010_BEGIN -->
Does Stripe have an option to use 1099-NEC instead of these two options?
<!-- SOURCE_TURN_010_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_010_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_010_END -->

## Turn 011 — assistant

- role: `assistant` — DO NOT EDIT
- has_answer: `"NOT_PRESENT"` — DO NOT EDIT

### English source — DO NOT EDIT

<!-- SOURCE_TURN_011_BEGIN -->
​
<!-- SOURCE_TURN_011_END -->

### Chinese translation — EDIT HERE

<!-- ZH_TURN_011_BEGIN -->
[待翻译：请只替换本行，保留上下边界标记]
<!-- ZH_TURN_011_END -->
