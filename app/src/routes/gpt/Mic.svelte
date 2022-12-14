<script lang="ts">
  import { onDestroy } from "svelte";
  import { RecordRTCPromisesHandler } from "recordrtc";
  import { PUBLIC_SERVER_DOMAIN } from "$env/static/public";

  export let handleTranscriptChange: (newTranscriptChuncks: string[], newInterim: string) => void;
  export let handlePause: () => void;
  export let handleClear: () => void;

  let socket: WebSocket | null = null;
  let recorder: RecordRTCPromisesHandler | null = null;
  let isRecording = false;
  let transcriptChunks: string[] = [];
  let interim = "";

  let showClosedWhileRecording = false;

  $: handleTranscriptChange(transcriptChunks, interim);

  function handleTranscriptAvailable(event: any) {
    interim = "";
    for (const result of event) {
      if (result.is_final) {
        transcriptChunks = [...transcriptChunks, result.transcript];
      } else {
        interim += result.transcript;
      }
    }
  }

  function openConnection() {
    console.log("Opening connection");
    socket = new WebSocket(`wss://${PUBLIC_SERVER_DOMAIN}/ws`);
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleTranscriptAvailable(data);
    };
    socket.onclose = () => {
      console.log("Connection closed");
      socket = null;
      if (isRecording) {
        isRecording = false;
        showClosedWhileRecording = true;
        setTimeout(() => {
          showClosedWhileRecording = false;
        }, 5000);
        console.log("connection closed while recording, retrying");
      }
    };
  }

  function onDataAvailable(audioChunk: Blob) {
    if (audioChunk.size > 0 && socket?.readyState === WebSocket.OPEN) {
      socket.send(audioChunk);
    }
  }

  async function initializeRecorder() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: false,
      });
      recorder = new RecordRTCPromisesHandler(stream, {
        type: "audio",
        mimeType: "audio/webm",
        timeSlice: 100,
        ondataavailable: onDataAvailable,
      });
      recorder.startRecording();
      isRecording = true;
    } catch (error) {
      console.error(error);
      alert("Either you don't have a microphone or you denied access to it.");
    }
  }

  async function handlePlayPause() {
    if (!recorder) {
      openConnection();
      initializeRecorder();
      return;
    }

    if (isRecording) {
      isRecording = false;
      socket?.close();
      await recorder.stopRecording();
      transcriptChunks = [...transcriptChunks, interim];
      interim = "";
      handlePause();
    } else {
      isRecording = true;
      openConnection();
      await recorder.startRecording();
    }
  }

  function clear() {
    transcriptChunks = [];
    interim = "";
    handleClear();
  }

  onDestroy(() => {
    console.log("Destroying recorder");
    if (recorder) {
      recorder?.destroy();
    }
  });
</script>

<div class="buttons">
  <button on:click={handlePlayPause}>{isRecording ? "pause" : "record"}</button>
  <button on:click={clear}>clear</button>
</div>
{#if showClosedWhileRecording}
  <div class="warning">
    <div class="dot" />
    <div>Recording paused after 5 minutes, press record to continue.</div>
  </div>
{/if}

<style>
  .warning {
    display: flex;
    align-items: center;
    margin: 1rem 0;
  }

  .dot {
    height: 10px;
    width: 10px;
    background-color: red;
    border-radius: 50%;
    display: inline-block;
    margin-right: 10px;
  }

  .buttons {
    display: flex;
    align-items: center;
    column-gap: 0.5rem;
  }

  button {
    display: inline-block;
    padding: 6px 10px;
    border: 1px solid #ccc;
    border-radius: 7px;
    cursor: pointer;
    background-color: #f0f0f0;
    font-size: 1rem;
  }
</style>
