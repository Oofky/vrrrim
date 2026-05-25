import { EditorView, basicSetup } from "codemirror";
import { vim } from "@replit/codemirror-vim";
import { javascript } from "@codemirror/lang-javascript";

const editorParent = document.getElementById("editor");

const view = new EditorView({
  doc: "// Welcome to the Vim terminal simulation\nconsole.log('Hello World');",
  extensions: [
    basicSetup,         // Essential editor features (line numbers, etc.)
    vim(),              // Enables Vim keybindings and status bar
    javascript(),       // Optional language syntax highlighting
  ],
  parent: editorParent,
});
