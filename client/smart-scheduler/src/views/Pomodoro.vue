<template>
    <ion-page>
      <ion-content class="ion-padding">
        <h1 class="title">Time to focus.</h1>
        <div class="timer-container">
          <h2>{{ isBreak ? "Break Time" : "Focus Time" }}</h2>
          <h1>{{ formattedTime }}</h1>
        </div>
        <ion-grid>
          <ion-row v-if="!isTimerRunning">
            <ion-col size="3">
              <ion-button expand="block" @click="setTimer(15)">15 Min</ion-button>
            </ion-col>
            <ion-col size="3">
              <ion-button expand="block" @click="setTimer(20)">20 Min</ion-button>
            </ion-col>
            <ion-col size="3">
              <ion-button expand="block" @click="setTimer(25)">25 Min</ion-button>
            </ion-col>
            <ion-col size="3">
              <ion-button expand="block" @click="setTimer(30)">30 Min</ion-button>
            </ion-col>
          </ion-row>
          <ion-row>
            <ion-col size="6">
              <ion-button expand="block" @click="startTimer" :disabled="isTimerRunning">Start</ion-button>
            </ion-col>
            <ion-col size="6">
              <ion-button expand="block" @click="pauseTimer" :disabled="!isTimerRunning">Pause</ion-button>
            </ion-col>
          </ion-row>
          <ion-row>
            <ion-col size="12">
              <ion-button expand="block" color="danger" @click="endSession">End Session</ion-button>
            </ion-col>
          </ion-row>
        </ion-grid>
      </ion-content>
    </ion-page>
  </template>
  
  <script>
  import {
    IonPage,
    IonContent,
    IonGrid,
    IonRow,
    IonCol,
    IonButton,
  } from "@ionic/vue";
  import { defineComponent } from "vue";
  
  export default defineComponent({
    components: {
      IonPage,
      IonContent,
      IonGrid,
      IonRow,
      IonCol,
      IonButton,
    },
    data() {
      return {
        time: 0,
        timer: null,
        isTimerRunning: false,
        isBreak: false,
      };
    },
    computed: {
      formattedTime() {
        const minutes = Math.floor(this.time / 60);
        const seconds = this.time % 60;
        return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
      },
    },
    methods: {
      setTimer(minutes) {
        this.time = minutes * 60;
      },
      startTimer() {
        if (this.timer) {
          clearInterval(this.timer);
        }
        this.isTimerRunning = true;
        this.timer = setInterval(() => {
          if (this.time > 0) {
            this.time -= 1;
          } else {
            clearInterval(this.timer);
            this.isTimerRunning = false;
            if (!this.isBreak) {
              this.isBreak = true;
              this.time = 5 * 60;
              this.startTimer();
            } else {
              this.isBreak = false;
            }
          }
        }, 1000);
      },
      pauseTimer() {
        if (this.timer) {
          clearInterval(this.timer);
        }
        this.isTimerRunning = false;
      },
      endSession() {
        if (this.timer) {
          clearInterval(this.timer);
        }
        this.isTimerRunning = false;
        this.isBreak = false;
        this.time = 0;
      },
    },
  });
  </script>
  
  <style scoped>
  .title {
    padding-top: 30px;
    font-size: 28px;
    font-weight: bold;
    text-align: left;
    padding-left: 25px;
  }
  .timer-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 200px;
    margin-bottom: 20px;
  }
  .timer-container h1 {
    font-size: 64px;
    margin: 0;
  }
  </style>
  