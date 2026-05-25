import {MergeView} from "https://esm.sh/@codemirror/merge"
import {EditorView, basicSetup} from "https://esm.sh/codemirror@6.0.2"
import {EditorState} from "https://esm.sh/@codemirror/state"

let doc = `class PostcardFile {
   private final Postcard postcard;
   public Postcard(Postcard postcard) {
      this.postcard = postcard;
   }
}
`

let view = new MergeView({
  a: {
    doc,
    extensions: basicSetup
  },
  b: {
    doc: doc.replace(/t/g, "T"),
    extensions: [
      basicSetup,
      EditorView.editable.of(false),
      EditorState.readOnly.of(true)
    ]
  },
  parent: document.getElementById("code-mirror-editor")
})
