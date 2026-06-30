I have all the information needed. Now I'll produce the complete, polished final guide with all 27 problems resolved inline, and any unfixable issues documented under Known Gaps.

---

# Getting Started with TypeScript: A Complete Beginner's Guide

---

## 1. What Is TypeScript?

TypeScript is a **statically typed superset of JavaScript**. Let's unpack that phrase:

- **JavaScript** is the programming language that runs in web browsers and on servers via Node.js. It is *dynamically typed*, meaning the type of a variable (whether it holds a number, a piece of text, or something else) is determined only when the program actually runs.
- **Statically typed** means the types are checked *before* the program runs — at the moment you compile your code.
- **Superset** means every program that is valid JavaScript is also valid TypeScript. You can take any existing `.js` file, rename it to `.ts`, and TypeScript will accept it.

TypeScript was created and is maintained by **Microsoft**. It was first released publicly in 2012 and has grown to become one of the most widely used languages in professional software development.

### Why Does TypeScript Exist?

In large JavaScript codebases, a common class of bug arises at *runtime* — meaning while users are actually running the software. For example, passing a number where a function expects a string might silently produce `NaN` (Not a Number, a special JavaScript value indicating an invalid arithmetic result) rather than throwing an obvious error. TypeScript catches these mistakes during development, before the code ever runs.

### How TypeScript Works

TypeScript files use the `.ts` extension. The TypeScript **compiler** — a program called `tsc` — reads your `.ts` files and **transpiles** them into plain `.js` files. **Transpilation** is the process of translating source code written in one language (TypeScript) into source code in another language that runs at a similar level of abstraction (JavaScript). This is different from traditional compilation, which translates high-level code all the way down to machine code. The JavaScript output is what actually runs in the browser or on a server.

When you run `tsc hello.ts`, the compiler creates a new file called `hello.js` **in the same folder as your `hello.ts` file**. You can then open that folder and see both files side by side. The `.js` file is what you run with Node.js or load in a browser.

This process involves **type erasure**: all TypeScript type information exists only at compile time and is completely removed from the output JavaScript. There is no runtime overhead — TypeScript's type safety is purely a development-time safety net.

```typescript
// ── JavaScript version (hello.js) ──────────────────────────
// No type information whatsoever.
let greeting = "Hello, world!";
console.log(greeting);

// ── TypeScript version (hello.ts) ──────────────────────────
// The `: string` part is a type annotation — it tells TypeScript
// what kind of value `greeting` is allowed to hold.
let greeting: string = "Hello, world!";
console.log(greeting);

// ── What the TypeScript compiler outputs (hello.js) ─────────
// Identical to plain JavaScript — the type annotation is erased.
let greeting = "Hello, world!";
console.log(greeting);
```

The compiled output is indistinguishable from JavaScript you would have written by hand. TypeScript adds nothing to the running program; it only helps you write it more safely.

---

## 2. Installation & Setup

### Prerequisites

Before installing TypeScript you need two tools:

- **Node.js** — a runtime that lets JavaScript run on your computer (outside a browser). Download the **LTS** (Long-Term Support) version from [https://nodejs.org](https://nodejs.org). LTS means the version is officially supported with bug fixes and security patches for an extended period — it is the safest choice for new projects.
- **npm** (Node Package Manager) — a tool that ships automatically with Node.js. It lets you install JavaScript and TypeScript packages from the internet.

### Opening a Terminal

A **terminal** (also called a command-line interface or shell) is a text-based window where you type commands directly to your computer. Here is how to open one on each operating system:

- **Windows:** Press `Win + R`, type `cmd`, and press Enter. Alternatively, search for "Command Prompt" or "Windows PowerShell" in the Start menu.
- **macOS:** Open Spotlight with `Cmd + Space`, type `Terminal`, and press Enter. You can also find Terminal in `Applications → Utilities → Terminal`.
- **Linux:** Press `Ctrl + Alt + T` on most distributions, or search for "Terminal" in your application launcher.

Once you have a terminal open, you type commands at the blinking cursor and press Enter to run them.

### Navigating Folders in a Terminal

Your terminal always has a **current working directory** — the folder it is currently "looking at." To move into a different folder, use the `cd` (change directory) command:

```bash
# Move into a folder called "my-project" that is inside your current folder.
cd my-project

# Move up one level to the parent folder.
cd ..

# On Windows, move to a full path.
cd C:\Users\YourName\Documents\my-project

# On macOS/Linux, move to a full path.
cd /Users/YourName/Documents/my-project
```

When you compile a TypeScript file, make sure your terminal is in the same folder as that file.

### Installing TypeScript Globally

Installing a package **globally** means it is installed once on your computer and the command it provides (`tsc` in this case) becomes available in any terminal window, in any folder. Without the `-g` flag, npm would install TypeScript only inside your current project folder, and `tsc` would not be recognised as a command outside of that folder.

```bash
# Install the TypeScript compiler globally on your machine.
# The -g flag = global installation, making `tsc` available everywhere.
npm install -g typescript
```

Verify the installation succeeded:

```bash
# Print the installed TypeScript version.
# Expected output example: Version 5.4.5
tsc --version
```

Verify Node.js and npm are installed by running:

```bash
# Print the installed Node.js version.
# Expected output example: v20.11.0
node --version

# Print the installed npm version.
# Expected output example: 10.2.4
npm --version
```

### Creating Your First TypeScript File

You need a **text editor** or **IDE** (Integrated Development Environment) to create and edit TypeScript files. A popular free choice is **Visual Studio Code** (VS Code), available at [https://code.visualstudio.com](https://code.visualstudio.com). VS Code has built-in TypeScript support and will highlight errors as you type.

To create the file, you have two options:

**Option A — Using your text editor:** Open VS Code (or any text editor), create a new file, paste in the code below, and save it as `hello.ts` in a folder of your choice (for example, `Documents/typescript-practice/hello.ts`).

**Option B — Using the terminal:** Navigate to the folder where you want the file, then run one of these commands depending on your operating system:

```bash
# macOS or Linux: creates an empty hello.ts file
touch hello.ts

# Windows Command Prompt: creates an empty hello.ts file
echo. > hello.ts
```

Then open the file in your text editor and add the following code:

```typescript
// hello.ts
// Declare a variable named `message` of type `string`
// and assign it the value "Hello, TypeScript!".
let message: string = "Hello, TypeScript!";

// Print the value of `message` to the terminal.
console.log(message);
```

### Compiling and Running

In your terminal, navigate to the folder containing `hello.ts` using the `cd` command shown above, then run:

```bash
# Compile hello.ts — this produces a new file called hello.js
# in the same folder as hello.ts.
tsc hello.ts

# Run the compiled JavaScript file with Node.js.
node hello.js
```

You should see the following output in your terminal:

```
Hello, TypeScript!
```

**✅ Mini Practice Checkpoint:** If you see `Hello, TypeScript!` printed in your terminal, your installation is working correctly. If you see an error, double-check that `tsc --version` returns a version number before continuing.

---

## 3. Basic Types

TypeScript includes several built-in types you will use constantly. This section covers the most important ones.

### Primitive Types

A **primitive type** is a basic, indivisible value. TypeScript's three core primitives map directly to JavaScript:

| Type | Represents | Example value |
|------|-----------|---------------|
| `string` | Text | `"hello"` |
| `number` | Any numeric value, including decimals | `42`, `3.14` |
| `boolean` | True or false | `true`, `false` |

**Type annotation syntax** follows this pattern:

```typescript
let variableName: type = value;
```

### Type Inference

**Type inference** is TypeScript's ability to automatically figure out the type of a variable from the value you assign to it — without you having to write the type annotation explicitly. For example, if you write `let score = 100;`, TypeScript sees the value `100` and *infers* (deduces) that `score` must be a `number`. You did not need to write `let score: number = 100;` — TypeScript worked it out for you.

Type inference is convenient, but explicit annotations are still valuable: they document your intent clearly and catch mistakes when you later assign the wrong kind of value.

### Special Types

- **`any`** — Tells TypeScript to stop checking this variable entirely. It effectively turns off type safety for that value. Avoid it wherever possible; using `any` defeats the purpose of TypeScript.
- **`unknown`** — A safer alternative to `any`. TypeScript will not let you perform operations on an `unknown` value until you first prove what type it is at runtime. The process of proving a type is called **type narrowing** — you "narrow" a broad, uncertain type down to a specific one by testing it with a conditional check (for example, checking whether a value is a string before treating it as one). See the code example below for a demonstration.
- **`void`** — Used as the return type of a function that does not return a meaningful value (for example, a function that only logs something to the terminal). See Section 4 for a full example.
- **`never`** — Represents a value that can never exist. Used in functions that always throw an error or run forever (and therefore never return), and in **exhaustive checks** — patterns that confirm every possible case in a type has been handled.

### The `typeof` Operator

**`typeof`** is a JavaScript operator that inspects a value at runtime and returns a string describing its type — for example, `"string"`, `"number"`, or `"boolean"`. It is the most common tool for type narrowing: you use it inside an `if` condition to tell TypeScript "in this branch, I have confirmed the type is X."

### Nullish Values

A value is called **nullish** if it is either `null` or `undefined`. Both represent the absence of a value:

- **`null`** means a value is *intentionally* absent — you or someone else deliberately set it to nothing.
- **`undefined`** means a variable has been declared but has not yet been assigned any value.

With TypeScript's strict mode enabled (a compiler option covered in Section 8 that turns on extra safety checks), `null` and `undefined` are treated as distinct types and cannot be accidentally assigned to a `string` or `number`.

### Arrays and Tuples

- An **array** is an ordered list of values of the same type. You can write it as `string[]` or equivalently as `Array<string>`.
- A **tuple** is a fixed-length array where each position has a specific, predetermined type. The length and the type of each position are fixed — you cannot add extra elements or swap the positions. Use a tuple when the number of elements and their types are known and must not change — for example, a pair of `[id, name]`.

```typescript
// types.ts — demonstrating TypeScript's basic types

// ── Primitives with explicit type annotations ─────────────────
let username: string = "Alice";          // must always be text
let age: number = 30;                    // integer or decimal
let isAdmin: boolean = false;            // only true or false

// ── Type inference (no annotation needed) ────────────────────
// TypeScript sees the value 42 and infers `score` is a number.
// This is equivalent to writing: let score: number = 42;
let score = 42;

// ── Arrays ───────────────────────────────────────────────────
let colors: string[] = ["red", "green", "blue"]; // array of strings
let counts: Array<number> = [1, 2, 3];           // alternative syntax

// ── Tuple ────────────────────────────────────────────────────
// Position 0 must be a number (the ID); position 1 must be a string (the name).
// The length is fixed at exactly 2 elements.
let user: [number, string] = [1, "Alice"];

// ── Type narrowing with typeof ────────────────────────────────
// `rawInput` might be anything — we don't know its type yet.
let rawInput: unknown = "hello from the server";

// `typeof rawInput` returns the string "string" at runtime.
// Inside this `if` block, TypeScript knows rawInput is a string,
// so it allows us to call string-only methods like .toUpperCase().
if (typeof rawInput === "string") {
  console.log(rawInput.toUpperCase()); // Output: HELLO FROM THE SERVER
}

// ── null and undefined (nullish values) ─────────────────────
let middleName: string | null = null;         // intentionally absent
let nickname: string | undefined = undefined; // not yet assigned

// ── void: a function that returns nothing ────────────────────
function printWelcome(name: string): void {
  // This function logs a message but does not return a value.
  console.log("Welcome, " + name + "!");
}

printWelcome("Alice"); // Output: Welcome, Alice!
```

---

## 4. Functions & Type Annotations

Functions are the building blocks of any program. TypeScript lets you annotate both what goes *into* a function (its **parameters**) and what comes *out* (its **return type**). Annotating both prevents silent bugs — for example, accidentally returning `undefined` when a number is expected.

### Annotating Parameters and Return Types

The syntax for annotating a function is:

```typescript
function functionName(param1: type1, param2: type2): returnType {
  // function body
}
```

Here is a concrete example — a function that adds two numbers and returns the result:

```typescript
// add.ts

// Both parameters are annotated as `number`.
// The return type after the closing parenthesis is also `number`.
// If you accidentally return a string here, TypeScript will error immediately.
function add(a: number, b: number): number {
  return a + b; // arithmetic on two numbers — safe and predictable
}

console.log(add(3, 4)); // Output: 7
```

### The `void` Return Type

When a function does not return a meaningful value — for example, a function that only logs something to the terminal — annotate its return type as **`void`**. You already saw a `void` example at the end of Section 3. Here it is again for clarity:

```typescript
// void-example.ts

// `void` tells TypeScript: "this function intentionally returns nothing."
function logMessage(message: string): void {
  console.log("LOG:", message);
  // No `return` statement — TypeScript is satisfied because the return type is void.
}

logMessage("Server started"); // Output: LOG: Server started
```

### Union Types

A **union type** uses the `|` (pipe) operator and means "this value can be one of these types." For example, `string | number` means the value is allowed to be either a string or a number — but nothing else. You write it by placing `|` between each permitted type. Union types appear frequently when a variable or parameter can legitimately hold more than one kind of value.

```typescript
// union-example.ts

// `id` can hold either a string or a number.
let id: string | number;
id = 101;        // valid — number
id = "user-101"; // also valid — string
```

### Optional and Default Parameters

- An **optional parameter** is marked with `?` after its name. It may or may not be provided by the caller. Inside the function, its value will be `undefined` if the caller did not supply it. **Optional parameters must always come *after* required parameters.** The compiler matches arguments to parameters left to right — if an optional parameter appeared first, TypeScript would have no way of knowing whether a missing argument was intentionally skipped or accidentally omitted.