<template>
  <ion-page>
    <ion-content class="ion-padding">
      <h1 class="schedulize">Schedulize</h1>
      <h2 class="subtext">Start optimizing your day.</h2>
      <div class="register-form">
        <form @submit.prevent="registerUser">
          <div class="form-group">
            <ion-label position="floating">First Name</ion-label>
            <ion-input v-model="firstName" type="text" required></ion-input>
          </div>
          <div class="form-group">
            <ion-label position="floating">Last Name</ion-label>
            <ion-input v-model="lastName" type="text" required></ion-input>
          </div>
          <div class="form-group">
            <ion-label position="floating">Email</ion-label>
            <ion-input v-model="email" type="email" required></ion-input>
          </div>
          <div class="form-group">
            <ion-label position="floating">Password</ion-label>
            <ion-input v-model="password" type="password" required></ion-input>
          </div>
          <div class="form-group">
            <ion-label position="floating">Confirm Password</ion-label>
            <ion-input
              v-model="confirmPassword"
              type="password"
              required
            ></ion-input>
          </div>
          <ion-button expand="block" type="submit" class="custom_button"
            >Register</ion-button
          >
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
} from "@ionic/vue";
import { defineComponent } from "vue";
export default defineComponent({
  components: { IonButton, IonLabel, IonInput, IonItem, IonContent, IonPage },
  data() {
    return {
      firstName: "",
      lastName: "",
      email: "",
      password: "",
      confirmPassword: "",
    };
  },
  methods: {
    async registerUser() {
      if (this.password !== this.confirmPassword) {
        alert("Passwords do not match");
        return;
      }
      try {
        // endpoint is /?
        const response = await fetch("http://localhost:8000/api/v1/users", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            first_name: this.firstName,
            last_name: this.lastName,
            email: this.email,
            password: this.password,
          }),
        });
        if (!response.ok) {
          throw new Error("Register failed");
        }
        console.log("Register successful");
        // Redirect to settings page if successful
        this.$router.push({ name: "Settings" });
      } catch (error) {
        console.error("Error during register:", error);
      }
    },
  },
});
</script>

<style scoped>
.register-form {
  padding-top: 40px;
  max-width: 350px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center; /* Center items horizontally */
}

.form-group {
  margin-bottom: 20px;
}

ion-label {
  font-weight: bold;
}

ion-input {
  border-radius: 5px;
}

ion-button:hover {
  --background: #0056b3;
}
.schedulize {
  padding-top: 30px;
  font-size: 30px;
  font-weight: bold;
  text-align: center;
}

.subtext {
  font-size: 20px;
  text-align: center;
}

.custom_button {
  --background: #75f4c7;
  width: 300px;
  color: #000000;
  font-weight: bold;
}

</style>
