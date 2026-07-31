# MailSentry AI

I want you to build a complete frontend for my SaaS application called MailSentry.

MailSentry is an AI-powered email assistant.

Current MVP only supports Email Spam Classification.

Future phases will include:

• Email Ranking

• AI Email Summary

• Meeting Scheduling

IMPORTANT:

Generate production-quality React code using:

- React + Vite

- Tailwind CSS

- React Router

- Axios

- React Hook Form

- Framer Motion

- Lucide React Icons

The project should have clean folder architecture and reusable components.

------------------------------------

Design Style

------------------------------------

The UI should look premium like:

- ChatGPT

- Linear

- Stripe Dashboard

- Vercel Dashboard

Theme:

Dark Mode

Primary Color:

#4F46E5

Accent:

#06B6D4

Background:

Almost black (#09090B)

Cards:

Rounded-xl

Blurred Glass effect

Soft shadows

Modern typography

Smooth animations

Minimalistic

Responsive

NO childish design.

Everything should feel enterprise level.

------------------------------------

Pages

------------------------------------

Create the following pages.

Landing Page

Features

Pricing

About

Contact

Login

Signup

Forgot Password

Reset Password

Email Verification

Dashboard

Profile

Settings

404 Page

------------------------------------

Navbar

------------------------------------

Logo

MailSentry

Links:

Home

Features

Pricing

About

Contact

Login

Signup

Dashboard (after login)

Responsive mobile menu.

------------------------------------

Landing Page

------------------------------------

Hero Section

Large heading

Protect your Inbox with AI

Subheading:

Detect spam emails instantly using Machine Learning.

Buttons:

Get Started

View Demo

Illustration on right side.

Feature Cards

How it Works

Why MailSentry

Testimonials

Pricing Preview

FAQ

Footer

------------------------------------

Dashboard

------------------------------------

Sidebar

Dashboard

Email Classifier

History

Profile

Settings

Logout

Top Bar

Search

Notifications

Profile Avatar

------------------------------------

Dashboard Home

------------------------------------

Statistics cards

Total Predictions

Spam Emails

Safe Emails

Accuracy

Recent Predictions Table

Quick Action buttons

------------------------------------

Email Classifier Page

------------------------------------

This is the main feature.

Create a modern form.

Fields:

Subject

Message

Predict Button

Loading animation

After clicking Predict:

Show beautiful result card.

If prediction == Spam

Display:

Red warning icon

Spam Email

Confidence %

Reason

If prediction == Ham

Green check icon

Safe Email

Confidence %

Reason

Result card should animate into view.

------------------------------------

History Page

------------------------------------

Modern table

Date

Subject

Prediction

Confidence

Search

Pagination

Filter

------------------------------------

Profile Page

------------------------------------

Avatar

Name

Email

Role

Edit profile button

------------------------------------

Settings

------------------------------------

Theme Toggle

Notification Settings

Security

Delete Account

------------------------------------

Authentication

------------------------------------

Beautiful login page

Email

Password

Remember Me

Forgot Password

Google Login button

Signup page

Name

Email

Password

Confirm Password

------------------------------------

Components

------------------------------------

Create reusable components.

Navbar

Footer

Sidebar

Button

Input

Textarea

Modal

Card

Loader

Toast

ResultCard

StatsCard

PredictionBadge

------------------------------------

Animations

------------------------------------

Use Framer Motion.

Page transitions

Fade

Slide

Hover

Card animation

Button animation

------------------------------------

API Integration

------------------------------------

Create an Axios service.

Base URL should come from

VITE_API_URL

Do NOT hardcode URLs.

Create API files.

authApi.js

predictionApi.js

historyApi.js

profileApi.js

------------------------------------

Prediction API

------------------------------------

POST

/api/v1/predict

Body:

{

subject:"",

message:""

}

Expected Response:

{

prediction:"Spam",

confidence:98.34,

reason:"Contains phishing keywords"

}

Show loading state.

Handle API errors.

------------------------------------

State Management

------------------------------------

Use React Context.

Auth Context

Prediction Context

------------------------------------

Folder Structure

------------------------------------

src/

components/

pages/

layouts/

hooks/

services/

context/

assets/

routes/

utils/

App.jsx

main.jsx

------------------------------------

Code Quality

------------------------------------

Reusable components

Clean architecture

Proper naming

Accessibility

Responsive

No duplicated code

------------------------------------

Output

------------------------------------

Generate the complete project one page at a time.

Always keep components reusable.

Never generate placeholder code if a reusable implementation can be created.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/44f300a7-dd7b-4a18-b7ef-87866ecd5387).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
