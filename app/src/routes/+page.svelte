<script lang="ts">
  import { goto } from "$app/navigation";
  import { user } from "@/store";

  let name: string;

  function onSubmit() {
    $user = name;
    goto("/gpt");
  }
</script>

<main>
  <h1>Welcome to Aphasia GPT</h1>

  <form on:submit|preventDefault={onSubmit}>
    <input type="text" bind:value={name} placeholder="Enter participant name" />
  </form>
</main>

<style>
  main {
    margin-top: 20vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  input {
    font-family: inherit;
    font-size: 1.5em;
    padding: 0.5em;
    border: 1px solid #ccc;
    border-radius: 7px;
    outline: none;
  }

  input::placeholder {
    color: #ccc;
    font-style: italic;
  }
</style>
