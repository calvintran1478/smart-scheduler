<template>
  <ion-page>
    <ion-content class="ion-padding">
      <div class="register-form">
        <h2>Register</h2>
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
            <ion-input v-model="confirmPassword" type="password" required></ion-input>
          </div>
          <ion-button expand="block" type="submit" class="custom_button">Register</ion-button>
        </form>
      </div>
    </ion-content>
  </ion-page>
</template>

<script>
export default {
  data() {
    return {
      firstName: '',
      lastName: '',
      email: '',
      password: '',
      confirmPassword: ''
    };
  },
  methods: {
    registerUser() {
      // Validate form fields before submitting the registration
      if (this.password !== this.confirmPassword) {
        alert("Passwords do not match");
        return;
      }
      // Your registration logic goes here
      console.log('Registering user with data:', {
        firstName: this.firstName,
        lastName: this.lastName,
        email: this.email,
        password: this.password
      });
    }
  }
};
</script>

<style scoped>
.register-form {
  max-width: 400px;
  margin: 0 auto;
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

ion-button {
  border-radius: 5px;
  --background: #007bff;
  color: #fff;
}

ion-button:hover {
  --background: #0056b3;
}
</style>
