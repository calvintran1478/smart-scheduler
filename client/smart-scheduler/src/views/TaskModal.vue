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
        <ion-select
          v-model="selectedTag"
          interface="popover"
          @ionChange="selectTag"
        >
          <ion-select-option v-for="tag in tags" :value="tag" :key="tag.name">
            {{ tag.name }}
          </ion-select-option>
        </ion-select>
        <ion-item v-if="creatingNewTag">
          <ion-label position="stacked">New Tag Name</ion-label>
          <ion-input
            v-model="newTagName"
            placeholder="Enter new tag name"
          ></ion-input>
        </ion-item>
        <ion-item v-if="creatingNewTag">
          <ion-label position="stacked">Tag Colour</ion-label>
          <ion-select v-model="newTagColour" interface="popover">
            <ion-select-option
              v-for="colour in basicColours"
              :value="colour"
              :key="colour"
            >
              <div
                :style="{
                  backgroundColour: colour,
                  width: '20px',
                  height: '20px',
                  display: 'inline-block',
                  marginRight: '5px',
                }"
              ></div>
              {{ colour }}
            </ion-select-option>
          </ion-select>
        </ion-item>
        <ion-button v-if="!creatingNewTag" @click="toggleCreateNewTag"
          >Add New Tag</ion-button
        >
      </ion-item>
      <ion-button expand="block" @click="createTask">Create Task</ion-button>
    </ion-content>
  </ion-modal>
</template>
  
  <script>
import {
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
  IonDatetime,
  IonSelect,
  IonSelectOption,
} from "@ionic/vue";
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
    IonDatetime,
    IonSelect,
    IonSelectOption,
  },
  props: {
    isOpen: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      name: "",
      date: new Date().toISOString(),
      time: "23:59:59",
      tags: [],
      selectedTag: null,
      creatingNewTag: false,
      newTagName: "",
      newTagColour: "",
      basicColours: ["red", "blue", "green", "yellow", "purple"],
    };
  },
  methods: {
    closeModal() {
      this.$emit("close");
    },
    async createTask() {
      const token = localStorage.getItem("token"); // Retrieve token from localStorage
      if (!token) {
        console.error("No token found");
        return;
      }
      console.log(token);
      let task = {
        name: this.name,
        deadline_date: this.date.split("T")[0],
        deadline_time: this.time,
      };

      if (this.selectedTag) {
        task.tag = this.selectedTag.name;
      } else if (this.creatingNewTag) {
        const newTag = {
          name: this.newTagName,
          colour: this.newTagColour,
        };

        try {
          const response = await fetch(
            "http://localhost:8000/api/v1/users/tags",
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
              },
              body: JSON.stringify(newTag),
            }
          );

          if (response.status === 201) {
            const createdTag = await response.json();
            task.tag = createdTag.name;
          } else {
            console.error("Failed to create tag:", response.statusText);
            return;
          }
        } catch (error) {
          console.error("Error creating tag:", error);
          return;
        }
      }

      try {
        const response = await fetch(
          "http://localhost:8000/api/v1/users/tasks",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify(task),
          }
        );

        if (response.status === 201) {
          const newTask = await response.json();
          this.$emit("task-created", newTask);
          this.closeModal();
        } else {
          console.error("Failed to create task:", response.statusText);
        }
      } catch (error) {
        console.error("Error creating task:", error);
      }
    },
    async fetchTags() {
      const token = localStorage.getItem("token");
      if (!token) {
        console.error("No token found");
        return;
      }

      try {
        const response = await fetch(
          "http://localhost:8000/api/v1/users/tags",
          {
            method: "GET",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (response.status === 200) {
          const data = await response.json();
          this.tags = data.tags;
        } else {
          console.error("Failed to fetch tags:", response.statusText);
        }
      } catch (error) {
        console.error("Error fetching tags:", error);
      }
    },
    async selectTag() {},
    toggleCreateNewTag() {
      this.creatingNewTag = true;
    },
  },
  mounted() {
    this.fetchTags();
  },
});
</script>
  
  <style scoped>
/* for styling later */
</style>
  