<template>
    <ion-modal :is-open="true" @didDismiss="closeModal">
      <ion-header>
        <ion-toolbar>
          <ion-title>Add Task</ion-title>
          <ion-buttons slot="end">
            <ion-button @click="closeModal">Close</ion-button>
          </ion-buttons>
        </ion-toolbar>
      </ion-header>
      <ion-content class="ion-padding">
        <ion-item>
          <ion-label position="stacked">Task Name</ion-label>
          <ion-input v-model="name" placeholder="Enter task name"></ion-input>
        </ion-item>
        <ion-item>
          <ion-label position="stacked">Due Date</ion-label>
          <ion-datetime display-format="YYYY-MM-DD" v-model="date"></ion-datetime>
        </ion-item>
        <ion-item>
          <ion-label position="stacked">Tag</ion-label> 
          <ion-input v-model="tag" placeholder="Enter task tag"></ion-input>
        </ion-item>
        <ion-button expand="block" @click="createTask">Create Task</ion-button>
      </ion-content>
    </ion-modal>
  </template>
  
  <script>
  import { IonModal, IonHeader, IonToolbar, IonTitle, IonButtons, IonButton, IonContent, IonItem, IonLabel, IonInput, IonDatetime } from "@ionic/vue";
  import { defineComponent } from "vue";
  
  export default defineComponent({
    components: {
      IonModal,
      IonHeader,
      IonToolbar,
      IonTitle,
      IonButtons,
      IonButton,
      IonContent,
      IonItem,
      IonLabel,
      IonInput,
      IonDatetime
    },
    props: {
      isOpen: {
        type: Boolean,
        required: true
      }
    },
    data() {
      return {
        name: '',
        date: '',
        time: '23:59:59',  // default time
        tag: ''  // colour? category?
      };
    },
    methods: {
      closeModal() {
        this.$emit('close');
      },
      async createTask() {
        const token = localStorage.getItem("token"); // Retrieve token from localStorage
      if (!token) {
        console.error("No token found");
        return;
      }
      console.log(token);
        const task = {
          name: this.name,
          deadline_date: this.date.split('T')[0],
          deadline_time: this.time,
          tag: this.tag
        };
  
        try {
          const response = await fetch('http://localhost:8000/api/v1/users/tasks', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(task)
          });
  
          if (response.status === 201) {
            const newTask = await response.json();
            this.$emit('task-created', newTask);
            this.closeModal();
          } else {
            console.error('Failed to create task:', response.statusText);
          }
        } catch (error) {
          console.error('Error creating task:', error);
        }
      }
    }
  });
  </script>
  
  <style scoped>
  /* for styling later */
  </style>
  