# Getting Started with TypeScript: A Complete Beginner's Guide

---

## 1. What Is TypeScript and Why Use It?

**TypeScript** is a *statically typed superset of JavaScript*. Let's unpack that phrase one term at a time:

- **JavaScript** is the programming language that powers interactivity on the web. It runs inside browsers (like Chrome and Firefox) and on servers (via a tool called Node.js). Even if you have never written it, you have definitely used software built with it.
- **Superset** means TypeScript *includes everything JavaScript can do* and then adds more on top. Every valid JavaScript program is automatically a valid TypeScript program — nothing is taken away.
- **Statically typed** means every variable has a declared *type* — such as "this holds a number" or "this holds text" — and that type is checked *before* the program runs, at a step called **compile time**. If you break a type rule, the compiler tells you immediately instead of letting a broken program run silently.

TypeScript is developed and maintained by Microsoft and has become one of the most popular languages in the web-development ecosystem.

### The TypeScript Compiler

TypeScript files use the `.ts` extension. Because browsers and Node.js cannot read `.ts` files directly, TypeScript must be **transpiled** into plain JavaScript (`.js` files) before it can run.

**Transpilation** is the process of automatically converting source code written in one language (TypeScript) into equivalent source code in another language (JavaScript). The word is a blend of "transform" and "compile." The tool that performs this conversion is called the **TypeScript compiler**, invoked with the command `tsc`. You write `.ts`; `tsc` outputs `.js`; then you run the `.js` file.

### Type Erasure

One important detail: after compilation, all type annotations are **erased** from the output. The compiled `.js` file contains no trace of TypeScript's extra syntax — it is plain JavaScript that runs anywhere JavaScript runs. This means TypeScript's type system is a *development-time safety net only*; it adds zero overhead to your running program.

### Key Benefits

| Benefit | What it means for you |
|---|---|
| **Early error detection** | Mistakes are caught before you run your program, not after. |
| **Improved IDE support** | Editors like VS Code can offer precise autocomplete and inline documentation because they understand the types. |
| **Self-documenting code** | Type annotations act as readable contracts: `age: number` instantly tells any reader what kind of value `age` holds. |

### TypeScript vs. JavaScript

Everything you know about JavaScript still applies — functions, loops, objects, arrays, `async/await` — all work identically. TypeScript simply adds an optional layer of type information on top. After compilation, that type information is erased and the output is standard JavaScript that runs in browsers, in Node.js, or in any JavaScript environment.

### Side-by-Side: No Types vs. Types

```javascript
// ── plain JavaScript ──────────────────────────────────────
// JavaScript has no way to express that `price` must be a number.
// Passing a string causes a silent bug at runtime.
function applyDiscount(price, discount) {
  return price - discount;
  // If price is the string "100", JavaScript tries to subtract 10
  // from text, which is undefined math. The result is NaN.
}

applyDiscount("100", 10);
// No error shown — JavaScript lets this through.
// The program keeps running but produces NaN as the result.
```

> **What is NaN?** `NaN` stands for "Not a Number." It is a special JavaScript value that means a mathematical operation produced a nonsensical result — for example, trying to subtract a number from a piece of text. The dangerous part is that JavaScript returns `NaN` *silently*: no error message, no crash. Your program continues running with a corrupted value, which can cause subtle, hard-to-find bugs far away from where the mistake actually happened.

```typescript
// ── TypeScript equivalent ─────────────────────────────────
// Parameters are annotated with types using the colon (:) syntax.
function applyDiscount(price: number, discount: number): number {
  return price - discount;  // TypeScript knows both values are numbers
}

applyDiscount("100", 10);
// ^^^ Compiler error: Argument of type 'string' is not assignable
//     to parameter of type 'number'.
// The mistake is caught BEFORE the program ever runs.
```

TypeScript detected the problem at compile time. JavaScript would have silently returned `NaN` at runtime, potentially corrupting data without any warning. This is what "safety guarantees" means in practice: the compiler acts as an automated code reviewer that catches whole categories of mistakes before they can reach your users.

---

## 2. Installation & Environment Setup

### Prerequisites

Before installing TypeScript you need two tools already present on your machine:

- **Node.js** — a runtime that lets JavaScript (and TypeScript, after compilation) run outside a browser. Download it from [nodejs.org](https://nodejs.org).
- **npm** (Node Package Manager) — a tool for installing JavaScript and TypeScript packages. npm is bundled with Node.js automatically; installing Node.js also installs npm.

#### Choosing the Right Node.js Version

On the Node.js download page you will see two options: **LTS** and **Current**.

- **LTS** stands for *Long-Term Support*. These versions receive bug fixes and security patches for several years, making them the safest choice for most projects. **Download the LTS version.**
- **Current** contains the very latest features but may receive breaking changes. Avoid it unless you have a specific reason.

After downloading, run the installer and accept the default options. No special configuration is required.

Verify both tools are installed by opening your **terminal** (the command-line application — Terminal on macOS/Linux, Command Prompt or PowerShell on Windows) and running:

```bash
# Check Node.js version — any version 16 or higher works well
node --version

# Check npm version — any version 8 or higher works well
npm --version
```

Both commands should print a version number (e.g., `v20.11.0`). If you see "command not found," the installation did not complete successfully — try reinstalling Node.js.

### Installing TypeScript

Install TypeScript **globally** — meaning it becomes available as a command in your terminal from *any* directory on your computer, not just inside one specific project folder:

```bash
# npm install   → tells npm to install a package
# -g            → the "global" flag; installs the package system-wide
# typescript    → the name of the package on the npm registry
npm install -g typescript
```

**What does "global" mean here?** When you install a package globally, npm places it in a central location on your system and registers its commands in your terminal's PATH (the list of places your terminal searches for commands). After this, typing `tsc` in any terminal window will work — just like typing `node` works after you install Node.js.

Verify the installation succeeded:

```bash
# Prints the installed TypeScript version, e.g. "Version 5.4.5"
tsc --version
```

### Creating Your First Project

```bash
# Create a new directory (folder) for your project
mkdir my-ts-project

# Move into that directory
cd my-ts-project

# Create a new, empty TypeScript source file called hello.ts
# On macOS/Linux:
touch hello.ts
# On Windows (Command Prompt or PowerShell):
echo. > hello.ts
```

> **What do `touch` and `echo.` do?** `touch` is a macOS/Linux command that creates an empty file if it does not already exist. Windows does not have `touch`, but `echo. > hello.ts` achieves the same result: it creates an empty file named `hello.ts`. Both commands simply create the file; neither writes any content into it.

Open `hello.ts` in your editor and add the following:

```typescript
// hello.ts
// This is a simple TypeScript program.

// `message` is declared with the `let` keyword and annotated as type `string`.
// `let` declares a variable — a named container for a value.
// A string is a sequence of text characters (letters, spaces, punctuation).
let message: string = "Hello, TypeScript!";

// `console.log` prints a value to the terminal.
console.log(message);
```

### Compiling and Running

```bash
# `tsc hello.ts` reads hello.ts and produces hello.js in the same folder
tsc hello.ts

# Inspect the compiled JavaScript output (optional but educational)
# On macOS/Linux:
cat hello.js
# On Windows:
type hello.js
```

> **What do `cat` and `type` do?** These are terminal commands that print the contents of a file directly into the terminal window so you can read them. `cat` is the macOS/Linux version; `type` is the Windows equivalent. Running either one here lets you see the JavaScript that `tsc` generated from your `.ts` file.

```bash
# Run the compiled JavaScript file with Node.js
node hello.js
# Output: Hello, TypeScript!
```

You have just completed the full **compile-and-run loop**: write `.ts` → compile with `tsc` → run `.js` with Node.

### ✅ Quick Practice Checkpoint

Before moving on to types, confirm your setup works end-to-end:

1. `hello.ts` exists and contains the code above.
2. Running `tsc hello.ts` produces a `hello.js` file with no errors.
3. Running `node hello.js` prints `Hello, TypeScript!` to your terminal.

If all three steps succeed, your environment is ready and you can proceed confidently to the next section.

### Introducing `tsconfig.json`

As projects grow, passing individual file names to `tsc` becomes unwieldy. A `tsconfig.json` file lets you store all compiler settings in one place.

**What is JSON?** JSON (JavaScript Object Notation) is a simple text format for storing structured data using key-value pairs, like a configuration file. A `tsconfig.json` file is just a text file that the TypeScript compiler reads to know how to behave — which files to compile, how strict to be, where to put the output, and so on. You will configure it in detail in Section 8. For now, know it exists and can be generated with:

```bash
# Generates a tsconfig.json with sensible defaults and explanatory comments
tsc --init
```

---

## 3. Basic Types

**Type annotations** tell TypeScript what kind of value a variable may hold. The syntax is always: `variableName: TypeName`.

### The `let` Keyword

In JavaScript and TypeScript, `let` declares a **variable** — a named storage location whose value can change over time. (You may also see `const`, which declares a value that cannot be reassigned after creation.) TypeScript adds type annotations on top of this: `let age: number = 30` says "create a variable named `age` that must always hold a number, and set its initial value to 30."

### Primitive Types

A **primitive** is a simple, indivisible value. TypeScript's three core primitives mirror JavaScript's:

| Type | What it holds | Example value |
|---|---|---|
| `string` | Text | `"Alice"` |
| `number` | Any numeric value (integer or decimal) | `42`, `3.14` |
| `boolean` | True or false only | `true`, `false` |

### Special Types: `any` and `unknown`

- **`any`** disables type checking for that variable entirely. TypeScript will accept any operation on it without complaint. Overusing `any` defeats the purpose of TypeScript — you lose the ability to catch mistakes at compile time, which is the main reason you are using TypeScript in the first place.
- **`unknown`** is the safer alternative. Like `any`, it can hold any value, but TypeScript *forces you to check the type* before performing operations on it. This keeps you safe while still allowing flexibility.

### `null` and `undefined`

- **`null`** means "intentionally no value" — a deliberate empty state.
- **`undefined`** means "a value has not been assigned yet."

With **strict null checks** enabled (covered in Section 8), TypeScript treats these as distinct types and prevents you from accidentally using a variable that might be null.

### Array Types

An array is an ordered list of values. TypeScript offers two equivalent syntaxes:

- `number[]` — array of numbers (preferred for readability)
- `Array<number>` — the generic form (covered in Section 7)

### Tuple Types

A **tuple** is a fixed-length array where each position has its own specified type. "Fixed-length" means the array must contain *exactly* that many elements — no more, no fewer. Unlike a regular array (which can hold any number of elements of the same type), a tuple enforces both the length and the type at each specific position.

**When would you use this?** Tuples are useful when you want to group a small, known set of related values together — for example, a coordinate pair `[x, y]` or a name-and-age pair `["Alice", 30]`. The compiler prevents you from mixing up the order or adding extra elements.

### Type Inference

**Type inference** means TypeScript deduces the type automatically from the value you assign, without requiring an explicit annotation. This reduces repetitive boilerplate while keeping all the safety benefits.

### Understanding `typeof` and Type Narrowing

JavaScript provides a built-in operator called `typeof` that returns the type of a value as a string at runtime (e.g., `typeof 42` returns `"number"`, `typeof "hello"` returns `"string"`). The `===` operator checks for *strict equality* — it checks both the value and the type without any automatic conversion.

When TypeScript sees an `if` statement that uses `typeof`, it performs **type narrowing**: it understands that inside the `if` block, the variable must be the type you checked for. This is how you safely use `unknown` variables.

```typescript
// ── Primitive types with explicit annotations ──────────────────────────
let username: string  = "Alice";       // Must always be text
let age: number       = 30;            // Must always be a number
let isActive: boolean = true;          // Must always be true or false

// ── The `let` keyword and type enforcement ─────────────────────────────
// `let` declares a variable. TypeScript enforces the type on every future
// assignment, not just the first one.
let city: string = "London";
// city = 42;  // ← Compiler ERROR: Type 'number' is not assignable
//             //   to type 'string'. You promised `city` holds text.

// ── The `any` type — use sparingly ────────────────────────────────────
let anything: any = "hello";
anything = 42;           // Allowed — any accepts everything
anything.toUpperCase();  // TypeScript won't warn even if this breaks at runtime

// ── The `unknown` type — safer than `any` ─────────────────────────────
let mystery: unknown = "world";
// mystery.toUpperCase();  // ← Compiler ERROR: must check type first

// `typeof mystery === "string"` uses the `typeof` operator to ask JavaScript
// "what type is this value right now?" and `===` to compare the result to
// the string "string". If the check passes, TypeScript NARROWS the type:
// it knows mystery must be a string inside this block, so it allows string
// methods like .toUpperCase().
if (typeof mystery === "string") {
  console.log(mystery.toUpperCase()); // Safe: prints "WORLD"
}

// ── Array types ────────────────────────────────────────────────────────
let scores: number[]      = [95, 87, 100]; // Only numbers allowed
let names: Array<string>  = ["Alice", "Bob"]; // Equivalent syntax

// ── Tuple type ─────────────────────────────────────────────────────────
// Exactly two elements: position 0 must be a string, position 1 a number.
let person: [string, number] = ["Alice", 30];
// person = [30, "Alice"];  // ← Compiler ERROR: wrong order of types

// ── Type inference (no annotation needed) ──────────────────────────────
// TypeScript sees the value "Bob" and infers `inferred` is type `string`.
// You never wrote `: string`, but the safety is identical.
let inferred = "Bob";
// inferred = 100;  // ← Compiler ERROR: Type 'number' is not assignable
//                  //   to type 'string'. TypeScript inferred the type and
//                  //   still enforces it on every subsequent assignment.
```

Every annotation is a promise to the compiler. Breaking that promise produces a clear, descriptive error before the program ever runs.

---

## 4. Functions & Type Annotations

Functions are the building blocks of any program. TypeScript lets you annotate both the **inputs** (parameters) and the **output** (return value