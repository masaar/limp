# LIMP
LIMP is a backend framework that is designed for use by Masaar for rapid app development. It uses `HTTP/2 websocket` as primary protocol of communication with clients. However, it also provides an `HTTP/1 GET` interface for additional communication windows.

# Features
## Modern
LIMP is based on modern approaches of apps development. It enables both backend developers and front-end developers with set of tools to achieve better and more from very simple and powerful set of tools.

## Type Driven
LIMP has sophisticated workflow to handle types. It has the tools to convert types when needed. And, it has the process to reject wrong data types. This gives developers huge relieve and peace of mind when developing complicated apps that require type accuracy.

## Advanced Users, Sessions and Privileges Control Out-of-the-Box
Apps development platforms and frameworks provide users and privileges control in various forms and levels. What makes LIMP approach unique and developer-friendly is the fact user-management has endless aspects, with the ability to extend it to your needs without a single edit on the original structure of LIMP. This means your app can always keep up-to-date with LIMP upstream, without compromising on your requirements for advanced user management options. All using simple tools that are available to all.

## Multi-Environment Ready
LIMP gives the developers the ability to get started with single app that is having the ability to run the exact same app on different [environments](/docs/api-package.md#envs) without any custom configurations.

## Test-Driven Development Out-of-the-Box
That's correct! You can now develop your app and [test](/docs/tests.md) it with minimal set of instructions in under 5 minutes.

## Easy to Install, Upgrade and deploy
LIMP has simple workflow to [set it up](/docs/quick-start.md). Upgrading it is also as simple as pulling latest version of LIMP from this repository, as well as the latest version of the packages your app uses for its functionalities. Deploying is as a simple as creating a [Docker](https://www.docker.com) image using the provided `Dockerfile`.

## Multi-language and Localisation-ready
Yes! No more dealing with custom handlers for multi-language apps. Your app is multi-language out-of-the-box. Not only this, but your app can keep adding locales and change them along the way. This is a paradise for developers working on global scale apps.

# Docs Index
* [Dependencies](/docs/dependencies.md)
* [Quick Start](/docs/quick-start.md)
* [Tutorial](/docs/tutorial.md)
* [Tests Workflow](/docs/tests.md)
* [Design your App](/docs/design-app.md)
* API References:
  * [Call](/docs/api-call.md)
  * [Package](/docs/api-package.md)
  * [Module](/docs/api-module.md)
  * [User and Session](/docs/api-user-session.md)
  * [Privilege](/docs/api-privilege.md)
  * [Realm Mode](/docs/api-realm.md)
* [Data Controller and Drivers](/docs/data-drivers.md)
* [Development Guidelines](/docs/dev-guide.md)
* [Building SDK](/docs/build-sdk.md)
* [Technical Specs](/docs/technical.md)
* [CLI Interface](/docs/cli.md)
* [Contribution Guidelines](/CONTRIBUTING.md)