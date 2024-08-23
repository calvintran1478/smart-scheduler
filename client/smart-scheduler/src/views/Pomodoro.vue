<template>
  <ion-page>
    <ion-content class="ion-padding">
      <h1 class="title">Time to focus.</h1>
      <ion-item>
        <ion-label>Select Task</ion-label>
        <ion-select v-model="selectedTask">
          <ion-select-option
            v-for="task in tasks"
            :key="task.task_id"
            :value="task"
            >{{ task.name }}</ion-select-option
          >
        </ion-select>
      </ion-item>
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
            <ion-button
              expand="block"
              @click="startTimer"
              :disabled="isTimerRunning"
              >Start</ion-button
            >
          </ion-col>
          <ion-col size="6">
            <ion-button
              expand="block"
              @click="pauseTimer"
              :disabled="!isTimerRunning"
              >Pause</ion-button
            >
          </ion-col>
        </ion-row>
        <ion-row>
          <ion-col size="12">
            <ion-button expand="block" color="danger" @click="endSession"
              >End Session</ion-button
            >
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
  IonItem,
  IonLabel,
  IonSelect,
  IonSelectOption,
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
    IonItem,
    IonLabel,
    IonSelect,
    IonSelectOption,
  },
  data() {
    return {
      time: 0,
      timer: null,
      isTimerRunning: false,
      isBreak: false,
      tasks: [],
      selectedTask: null,
    };
  },
  computed: {
    formattedTime() {
      const minutes = Math.floor(this.time / 60);
      const seconds = this.time % 60;
      return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(
        2,
        "0"
      )}`;
    },
  },
  methods: {
    async fetchTasks() {
      try {
        const response = await fetch(
          "http://localhost:8000/api/v1/users/tasks",
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem("token")}`,
            },
          }
        );
        if (response.ok) {
          this.tasks = await response.json();
        } else {
          console.error("Failed to fetch tasks");
        }
      } catch (error) {
        console.error("Error fetching tasks:", error);
      }
    },
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
    async endSession() {
      if (this.timer) {
        clearInterval(this.timer);
      }
      this.isTimerRunning = false;
      this.isBreak = false;

      // record time spent on task
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const token = localStorage.getItem("token");
      if (!token) {
        console.error("No token found");
        return;
      }
      const response = await fetch(
        `http://localhost:8000/api/v1/users/tasks/${taskId}`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          credentials: "include",
          body: JSON.stringify({
            minutes_completed: this.time/60,
            timezone: timezone,
          }),
        }
      );
      if (response.ok) {
        console.log("Updated task successfully.")
      } else {
        throw new Error("Failed to update task.");
      }
      this.time = 0;
    },
  },
  mounted() {
    this.fetchTasks();
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
  