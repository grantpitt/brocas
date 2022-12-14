<script lang="ts">
  import { goto } from "$app/navigation";
  import { user } from "@/store";
  import { onMount } from "svelte";
  import { browser } from "$app/environment";
  import Mic from "./Mic.svelte";
  import { throttle } from "lodash";
  import { PUBLIC_SERVER_DOMAIN } from "$env/static/public";

  let time = new Date();

  let transcriptChunks: string[] = [];
  let interim = "";
  $: [displayTranscript, displayInterim] = formatTranscriptToDisplay(transcriptChunks, interim);

  $: console.log(transcriptChunks.join("") + interim);

  let cleanTranscripts: string[] = [];

  const minCleanWordCount = 5;
  const maxCleanWordCount = 10;

  const throttledCleanAndPredict = throttle(
    (fullTranscript) => cleanAndPredict(fullTranscript),
    2000
  );

  function handleTranscriptChange(newTranscriptChuncks: string[], newInterim: string) {
    transcriptChunks = newTranscriptChuncks;
    interim = newInterim;
    const fullTranscript = transcriptChunks.join(" ") + interim;
    if (fullTranscript.length > 0) {
      throttledCleanAndPredict(fullTranscript);
    }
  }

  function handlePause() {
    throttledCleanAndPredict.cancel();
  }

  function handleClear() {
    transcriptChunks = [];
    interim = "";
    cleanTranscripts = [];
  }

  async function cleanAndPredict(rawTranscript: string) {
    const words = rawTranscript.split(" ");
    if (words.length < minCleanWordCount) {
      return [];
    }
    const recentRawTranscript = words.slice(-maxCleanWordCount).join(" ");
    const responce = await fetch(`https://${PUBLIC_SERVER_DOMAIN}/clean`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      // TODO: Send user and time
      body: JSON.stringify({
        username: $user,
        timestamp: time.toLocaleTimeString(),
        raw_transcript: recentRawTranscript,
      }),
    });
    const result = await responce.json();

    cleanTranscripts = result.cleaned;
  }

  function formatTranscriptToDisplay(transcriptChunks: string[], interim: string) {
    const numWords = 25;
    const transcriptWords = transcriptChunks.join(" ").split(" ");
    const intermWords = interim.split(" ");
    const displayIntermWords = intermWords.slice(-numWords);
    const numTranscriptWords = Math.max(0, numWords - displayIntermWords.length);
    const displayTranscriptWords =
      numTranscriptWords === 0 ? [] : transcriptWords.slice(-numTranscriptWords);
    return [displayTranscriptWords.join(" "), displayIntermWords.join(" ")];
  }

  onMount(async () => {
    const interval = setInterval(() => {
      time = new Date();
    }, 1000);

    return () => {
      clearInterval(interval);
    };
  });
</script>

<main>
  <header>
    <!-- svelte-ignore missing-declaration -->
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <div on:click={() => goto("/")} class="user">
      {#if $user}
        {$user}
      {:else}
        *Not logged in
      {/if}
    </div>

    <div class="time">{time.toLocaleTimeString()}</div>
  </header>

  <div>
    {#if browser}
      <Mic {handleTranscriptChange} {handlePause} {handleClear} />
    {/if}
  </div>
  <section>
    <article class="clean">
      <h2>Cleaned and predicted</h2>
      <div class="options">
        {#await cleanTranscripts}
          <div />
        {:then cleanTranscriptsResults}
          {#each cleanTranscriptsResults as cleanTranscript, i}
            <div class="option">
              <div class="text">{cleanTranscript}</div>
            </div>
          {/each}
        {/await}
      </div>
    </article>
    <article class="transcript">
      <div>
        {displayTranscript}<span class="interim">{displayInterim}</span>
      </div>
      <article />
    </article>
  </section>
</main>

<style>
  header {
    display: inline-flex;
    align-items: center;
    column-gap: 10px;
    margin-bottom: 2rem;
  }

  .user {
    display: inline-block;
    cursor: pointer;
    padding: 4px 10px;
    border: 1px solid #ccc;
    border-radius: 7px;
  }

  .time {
    font-size: 0.9em;
    color: #bbb;
  }

  main {
    min-height: 100vh;
    display: flex;
    flex-direction: column;

    width: 100%;
    max-width: 1400px;
    margin: 0 auto;
    padding: 1rem 2rem;
    box-sizing: border-box;
  }

  section {
    margin: 1rem 0;
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }

  article h2 {
    color: #ccc;
    font-size: 1.5rem;
    font-weight: 800;
    margin: 0 0 0.5rem;
  }

  article.transcript {
    border-top: 1px dashed #ccc;
    min-height: 100px;
    padding: 1rem 0;
    font-size: 0.85rem;
  }

  .text {
    font-size: 1rem;
    font-weight: 500;
  }

  .interim {
    color: #bbb;
  }

  .options {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  @media (max-width: 1000px) {
    section {
      grid-template-columns: 1fr;
    }
  }
</style>
