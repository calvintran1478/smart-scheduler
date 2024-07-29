<template>
  <ion-page>
    <ion-content class="ion-padding">
      <h1 class="welcome">Hey,<br />Welcome to Schedulize!</h1>
      <h2 class="subtext">
        Tell us a bit about yourself so we can personalize your timetable.
      </h2>
      <div class="settings-form">
        <form @submit.prevent="userSettings">
          <div class="form-group">
            <ion-label position="floating">When you usually wake up?</ion-label>
            <ion-input v-model="wake_up_time" type="time" required></ion-input>
          </div>
          <div class="form-group">
            <ion-label position="floating">When do you usually sleep?</ion-label>
            <ion-input v-model="sleep_time" type="time" required></ion-input>
          </div>
          <div class="form-group">
            <ion-label position="floating">What time range do you focus best?</ion-label>
            <div class="time-range">
              <span>Start </span>
              <ion-input v-model="best_focus_time_start" type="time" required></ion-input>
              <span>End </span>
              <ion-input v-model="best_focus_time_end" type="time" required></ion-input>
            </div>
          </div>
          <div class="form-group">
            <ion-label position="floating">When do you start working?</ion-label>
            <ion-input v-model="start_of_work_day" type="time" required></ion-input>
          </div>
          <div class="form-group">
            <ion-label position="floating">When do you end working?</ion-label>
            <ion-input v-model="end_of_work_day" type="time" required></ion-input>
          </div>
          <div class="form-group">
            <ion-label>How long of a break (in minutes) do you like to take between work sessions?</ion-label>
            <ion-select v-model="break_length" interface="popover">
              <ion-select-option v-for="minutes in 61" :value="minutes - 1" :key="minutes">
                {{ minutes - 1 }}
              </ion-select-option>
            </ion-select>
          </div>
          <ion-button expand="block" type="submit" class="custom_button">Continue</ion-button>
        </form>
      </div>
    </ion-content>
  </ion-page>
</template>

<script>
import {
  IonButton,
  IonLabel,
  IonInput,
  IonItem,
  IonContent,
  IonPage,
  IonSelect,
  IonSelectOption
} from "@ionic/vue";
import { defineComponent } from "vue";

export default defineComponent({
  components: {
    IonButton,
    IonLabel,
    IonInput,
    IonItem,
    IonContent,
    IonPage,
    IonSelect,
    IonSelectOption
  },
  data() {
    return {
      wake_up_time: "",
      sleep_time: "",
      best_focus_times: [""],
      start_of_work_day: "",
      end_of_work_day: "",
      break_length: "",
      best_focus_time_start: "",
      best_focus_time_end: ""
    };
  },
  methods: {
    async userSettings() {
      const token = localStorage.getItem("token"); // Retrieve token from localStorage
      if (!token) {
        console.error("No token found");
        return;
      }
      try {
        const response = await fetch(
          "http://localhost:8000/api/v1/users/preferences/",
          {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${token}`
            },
            credentials: "include",
            body: JSON.stringify({
              wake_up_time: this.wake_up_time,
              sleep_time: this.sleep_time,
              start_of_work_day: this.start_of_work_day,
              end_of_work_day: this.end_of_work_day,
              best_focus_times: [`${this.best_focus_time_start} - ${this.best_focus_time_end}`],
              break_length: this.break_length,
            })
          }
        );
        if (response.status === 201 || response.status === 204) {
          console.log("Settings successful");
          // Redirect to home page if successful
          this.$router.push('/home');
        } else {
          throw new Error("Settings failed");
        }
      } catch (error) {
        console.error("Error during settings:", error);
      }
    }
  }
});
</script>

<style scoped>
.settings-form {
  padding-top: 40px;
  max-width: 300px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.form-group {
  margin-bottom: 20px;
}

ion-input {
  border-radius: 5px;
}

ion-button:hover {
  --background: #0056b3;
}

.welcome {
  padding-top: 30px;
  font-size: 28px;
  font-weight: bold;
  text-align: left;
  padding-left: 25px;
}

.subtext {
  font-size: 20px;
  text-align: left;
  padding-left: 25px;
}

.custom_button {
  --background: #75f4c7;
  width: 300px;
  color: #000000;
  font-weight: bold;
}

.time-range {
  display: flex;
  align-items: center;
}
</style>
