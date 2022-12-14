<slot />

<style global>
  @import url("https://rsms.me/inter/inter.css");

  :root {
    font-family: "Inter", sans-serif;
  }
  @supports (font-variation-settings: normal) {
    :root {
      font-family: "Inter var", sans-serif;
    }
  }

  * {
    box-sizing: border-box;
  }

  :global(body) {
    margin: 0;
    padding: 0;
    background: #fafafa;
    color: #333;
    line-height: 1.4;
  }
</style>
